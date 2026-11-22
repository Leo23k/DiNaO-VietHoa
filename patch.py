"""Patcher Việt hoá cho Diplomacy is Not an Option.

Cách dùng:
    python patch.py "<thư mục game>"            # cài Việt hoá
    python patch.py "<thư mục game>" --restore  # khôi phục bản gốc
"""
import json, os, re, shutil, sys

import numpy as np
import freetype
import UnityPy
from PIL import Image
from scipy.ndimage import distance_transform_edt as edt
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

HERE = os.path.dirname(os.path.abspath(__file__))
TTF = os.path.join(HERE, "data", "PatrickHand-Regular.ttf")
VI_JSON = os.path.join(HERE, "data", "vi.json")
EN_JSON = os.path.join(HERE, "data", "en_source.json")
BACKUP_DIR = "_backup_viethoa"
STAMP = "patched.json"  # ghi kích thước + thời gian sửa của file đã patch

AA = os.path.join("StreamingAssets", "aa", "StandaloneWindows64")
TARGETS = [
    os.path.join(AA, "localization-string-tables-english_assets_all.bundle"),
    os.path.join(AA, "settings_assets_all.bundle"),
    "resources.assets",
    "sharedassets0.assets",
]
SKIP_FONTS = ("Asian", "Noto", "Japan", "Korean", "Emoji")

# ---------------------------------------------------------------- tiện ích

def find_data_dir(game_dir):
    if game_dir.endswith("_Data") and os.path.isdir(game_dir):
        return game_dir
    for f in os.listdir(game_dir):
        if f.endswith("_Data") and os.path.isdir(os.path.join(game_dir, f)):
            return os.path.join(game_dir, f)
    sys.exit("Không tìm thấy thư mục *_Data trong: " + game_dir)


def load(path, data_dir):
    env = UnityPy.load(path)
    # lấy phiên bản Unity thật của game để vẫn chạy được khi game nâng cấp engine
    ver = UnityPy.load(os.path.join(data_dir, "globalgamemanagers")).file.unity_version
    gen = TypeTreeGenerator(ver)
    gen.load_local_game(os.path.dirname(data_dir))
    env.typetree_generator = gen
    return env


def save(env, path):
    data = env.file.save(packer="lz4") if path.endswith(".bundle") else env.file.save()
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)

# ---------------------------------------------------------------- bản dịch

def patch_text(env):
    vi = json.load(open(VI_JSON, encoding="utf8"))
    en_src = json.load(open(EN_JSON, encoding="utf8")) if os.path.exists(EN_JSON) else {}
    todo = {}
    n = 0
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            t = o.read_typetree()
        except Exception:
            continue
        if "m_TableData" not in t:
            continue
        for e in t["m_TableData"]:
            k = f'{t["m_Name"]}|{e["m_Id"]}'
            en = e["m_Localized"]
            # chỉ dùng bản dịch khi tiếng Anh gốc chưa đổi so với lúc dịch
            if k in vi and (not en_src or en_src.get(k) == en):
                e["m_Localized"] = vi[k]
                n += 1
            elif en.strip():
                todo[k] = en
        o.save_typetree(t)
    print(f"  đã thay {n} dòng chữ")
    out = os.path.join(HERE, "can_dich.json")
    if todo:
        json.dump(todo, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
        print(f"  {len(todo)} dòng mới/đã đổi chưa có bản dịch -> {out}")
    elif os.path.exists(out):
        os.remove(out)


def merge(path):
    """Gộp bản dịch mới {key: tiếng Việt} vào data/vi.json, cập nhật en_source theo can_dich.json."""
    vi = json.load(open(VI_JSON, encoding="utf8"))
    en_src = json.load(open(EN_JSON, encoding="utf8")) if os.path.exists(EN_JSON) else {}
    new = json.load(open(path, encoding="utf8"))
    todo_path = os.path.join(HERE, "can_dich.json")
    todo = json.load(open(todo_path, encoding="utf8")) if os.path.exists(todo_path) else {}
    tag = re.compile(r"\{[^}]*\}|<[^>]*>")
    ok = bad = 0
    for k, v in new.items():
        src = todo.get(k, en_src.get(k))
        if src is not None and sorted(tag.findall(src)) != sorted(tag.findall(v)):
            print("  bỏ qua (thẻ không khớp):", k)
            bad += 1
            continue
        vi[k] = v
        if src is not None:
            en_src[k] = src
        ok += 1
    json.dump(vi, open(VI_JSON, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    json.dump(en_src, open(EN_JSON, "w", encoding="utf8"), ensure_ascii=False, indent=0)
    print(f"Đã gộp {ok} dòng, bỏ qua {bad}. Chạy lại patch để áp dụng.")

# ---------------------------------------------------------------- font

face = freetype.Face(TTF)
UPM = face.units_per_EM
SS = 4  # siêu lấy mẫu khi tạo SDF
EXTRA = (set(range(0x20, 0x7F)) | set(range(0xA0, 0x1B1)) | set(range(0x1EA0, 0x1EFA))
         | set(range(0x300, 0x324)) | {0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026, 0x2022})


def render(cp, ps, pad):
    face.set_pixel_sizes(0, ps * SS)
    gi = face.get_char_index(cp)
    face.load_glyph(gi, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
    g = face.glyph
    b = g.bitmap
    adv = g.advance.x / 64 / SS
    if b.width == 0 or b.rows == 0:
        return gi, None, dict(w=0, h=0, bx=0, by=0, adv=adv)
    a = np.array(b.buffer, dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
    w, h, P = -(-b.width // SS), -(-b.rows // SS), pad * SS
    big = np.zeros((h * SS + 2 * P, w * SS + 2 * P), bool)
    big[P:P + b.rows, P:P + b.width] = a > 127
    d = (edt(big) - edt(~big)) / SS
    d = d.reshape(h + 2 * pad, SS, w + 2 * pad, SS).mean(axis=(1, 3))
    v = np.clip(0.5 + d / (2 * (pad + 1)), 0, 1)
    return gi, (v * 255).astype(np.uint8), dict(w=w, h=h, bx=g.bitmap_left / SS, by=g.bitmap_top / SS, adv=adv)


def build_atlas(t, W, H):
    pad = t["m_AtlasPadding"]
    ps = t["m_FaceInfo"]["m_PointSize"]
    cps = sorted({c["m_Unicode"] for c in t["m_CharacterTable"]} | EXTRA)
    cps = [c for c in cps if c in (0, 9, 10, 13) or face.get_char_index(c)]
    while True:
        img = np.zeros((H, W), np.uint8)
        x = y = rowh = 0
        glyphs, chars, used, ok = {}, [], [], True
        for cp in cps:
            if cp <= 31:
                gi, bm, m = 100000 + cp, None, dict(w=0, h=0, bx=0, by=0, adv=0)
            else:
                gi, bm, m = render(cp, ps, pad)
            if gi not in glyphs:
                rect = (0, 0, 0, 0)
                if bm is not None:
                    bh, bw = bm.shape
                    if x + bw > W:
                        x, y, rowh = 0, y + rowh, 0
                    if y + bh > H:
                        ok = False
                        break
                    img[y:y + bh, x:x + bw] = bm
                    rect = (x + pad, H - (y + bh) + pad, m["w"], m["h"])
                    used.append((x, H - (y + bh), bw, bh))
                    x += bw
                    rowh = max(rowh, bh)
                glyphs[gi] = {
                    "m_Index": gi,
                    "m_Metrics": {"m_Width": float(m["w"]), "m_Height": float(m["h"]),
                                  "m_HorizontalBearingX": float(m["bx"]), "m_HorizontalBearingY": float(m["by"]),
                                  "m_HorizontalAdvance": float(m["adv"])},
                    "m_GlyphRect": {"m_X": rect[0], "m_Y": rect[1], "m_Width": rect[2], "m_Height": rect[3]},
                    "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0}
            chars.append({"m_ElementType": 1, "m_Unicode": cp, "m_GlyphIndex": gi, "m_Scale": 1.0})
        if ok:
            break
        ps = int(ps * 0.92)

    s = ps / UPM
    fi = t["m_FaceInfo"]
    r = ps / fi["m_PointSize"]
    for k, v in list(fi.items()):
        if isinstance(v, float) and k != "m_Scale":
            fi[k] = v * r

    def height(ch):
        face.set_char_size(UPM * 64)
        face.load_char(ch, freetype.FT_LOAD_NO_SCALE)
        return face.glyph.metrics.horiBearingY * s

    fi.update({"m_FamilyName": "Patrick Hand", "m_StyleName": "Regular", "m_PointSize": ps, "m_UnitsPerEM": UPM,
               "m_AscentLine": face.ascender * s, "m_DescentLine": face.descender * s,
               "m_LineHeight": face.height * s, "m_CapLine": height("H"), "m_MeanLine": height("x"),
               "m_Baseline": 0.0})
    t["m_AtlasPopulationMode"] = 0
    t["m_GlyphTable"] = list(glyphs.values())
    t["m_CharacterTable"] = chars
    t["m_UsedGlyphRects"] = [{"m_X": a, "m_Y": b, "m_Width": c, "m_Height": d} for a, b, c, d in used]
    t["m_FreeGlyphRects"] = []
    t["m_KerningTable"] = {"kerningPairs": []}
    t["m_FontFeatureTable"] = {"m_GlyphPairAdjustmentRecords": []}
    if "m_CreationSettings" in t:
        t["m_CreationSettings"]["pointSize"] = ps
    return img


def patch_fonts(env):
    ttf = open(TTF, "rb").read()
    objs = {o.path_id: o for o in env.objects}
    for o in env.objects:
        if o.type.name == "Font":
            t = o.read_typetree()
            t["m_FontData"] = list(ttf)
            t["m_FontNames"] = ["Patrick Hand"]
            o.save_typetree(t)
            print("  Font:", t["m_Name"])
            continue
        if o.type.name != "MonoBehaviour":
            continue
        try:
            t = o.read_typetree()
        except Exception:
            continue
        if "m_GlyphTable" not in t or "m_AtlasPadding" not in t or any(x in t["m_Name"] for x in SKIP_FONTS):
            continue
        ref = t["m_AtlasTextures"][0]
        if ref["m_FileID"] != 0 or ref["m_PathID"] not in objs:
            continue
        tex = objs[ref["m_PathID"]].read()
        img = build_atlas(t, tex.m_Width, tex.m_Height)
        o.save_typetree(t)
        tex.image = Image.merge("RGBA", [Image.fromarray(img)] * 4)
        tex.save()
        print("  TMP font:", t["m_Name"])

# ---------------------------------------------------------------- main

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--merge":
        return merge(sys.argv[2])
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    data_dir = find_data_dir(sys.argv[1])
    backup = os.path.join(os.path.dirname(data_dir), BACKUP_DIR)

    if "--restore" in sys.argv:
        for rel in TARGETS:
            src = os.path.join(backup, rel)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(data_dir, rel))
                print("Khôi phục:", rel)
        print("Xong.")
        return

    stamp_path = os.path.join(backup, STAMP)
    stamp = json.load(open(stamp_path)) if os.path.exists(stamp_path) else {}
    for rel in TARGETS:
        src = os.path.join(data_dir, rel)
        dst = os.path.join(backup, rel)
        if not os.path.exists(src):
            sys.exit("Thiếu file: " + src)
        st = os.stat(src)
        is_ours = stamp.get(rel) == [st.st_size, int(st.st_mtime)]
        # file không phải do patcher ghi -> bản gốc (mới cài hoặc game vừa cập nhật)
        if not os.path.exists(dst) or not is_ours:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            print("Sao lưu bản gốc:", rel)

    for rel in TARGETS:
        print("Đang xử lý", rel, "...")
        # luôn đọc từ bản gốc để chạy lại nhiều lần vẫn an toàn; chép bản gốc vào cạnh file game
        # để UnityPy tìm được các file phụ thuộc (globalgamemanagers.assets...) cùng thư mục
        out = os.path.join(data_dir, rel)
        src = out + ".viethoa_src"
        shutil.copy2(os.path.join(backup, rel), src)
        try:
            env = load(src, data_dir)
            if "localization-string-tables" in rel:
                patch_text(env)
            else:
                patch_fonts(env)
            save(env, out)
            del env
        finally:
            import gc; gc.collect()
            try:
                os.remove(src)
            except OSError:
                pass
        st = os.stat(out)
        stamp[rel] = [st.st_size, int(st.st_mtime)]
        json.dump(stamp, open(stamp_path, "w"))
    print("Hoàn tất! Vào Settings > Language > English để chơi bản tiếng Việt.")


if __name__ == "__main__":
    main()
