# Hướng dẫn cho Claude: tiếp tục Việt hoá

Repo này là patcher Việt hoá cho game Unity **Diplomacy is Not an Option**. Repo không chứa file nào của game.

## Cấu trúc
- `patch.py`: patcher duy nhất. Có 3 chế độ: cài (`<thư mục game>`), khôi phục (`--restore`), gộp bản dịch (`--merge file.json`).
- `data/vi.json`: bản dịch, dạng `{"<Bảng>|<m_Id>": "tiếng Việt"}`. Ví dụ bảng: `CutScenes_en`, `UI_en`, `Missions_en`, `Buildings_en`, `Hints_en`, `Units_en`, `Researches_en`, `Tutorial_en`, `Environments_en`, `Diseases_en`.
- `data/en_source.json`: bản tiếng Anh gốc tại thời điểm dịch, cùng key với `vi.json`. Patcher chỉ dùng bản dịch khi tiếng Anh trong game vẫn trùng với file này.
- `data/PatrickHand-Regular.ttf`: font dùng cho toàn bộ chữ Latin (theo yêu cầu của chủ repo).

## Cách patcher hoạt động
- **Bản dịch:** ghi đè lên bảng English trong `StreamingAssets/aa/StandaloneWindows64/localization-string-tables-english_assets_all.bundle`. Addressables không kiểm tra CRC (`m_Crc` bằng 0), nên sửa bundle không bị chặn.
- **Font:** tạo lại atlas SDF tĩnh bằng Patrick Hand (freetype, siêu lấy mẫu 4 lần, EDT) cho mọi `TMP_FontAsset` trong `settings_assets_all.bundle`, `resources.assets` và `sharedassets0.assets`. Giữ nguyên kích thước atlas, padding và material; tự giảm cỡ mẫu nếu atlas không đủ chỗ. Bỏ qua các font Asian/Noto/Japan/Korean/Emoji. Các object `Font` thường được thay thẳng dữ liệu TTF.
- **Typetree:** `.assets` không nhúng typetree, nên dùng `TypeTreeGeneratorAPI` đọc từ `Managed/*.dll`, với phiên bản Unity lấy từ `globalgamemanagers`.
- **Sao lưu:** bản gốc nằm trong `<game>/_backup_viethoa/`, kèm file `patched.json` ghi kích thước và mtime của file đã patch. File trong game không khớp `patched.json` thì được coi là bản gốc mới (game vừa cập nhật) và được sao lưu lại. Patcher luôn đọc từ bản sao lưu, nên chạy lại nhiều lần vẫn an toàn.

## Quy trình khi game có bản mới
1. `pip install -r requirements.txt`, rồi `python patch.py "<thư mục game>"`.
2. Nếu có `can_dich.json` (dạng `{key: tiếng Anh}` cho các dòng mới hoặc đã đổi): chia nhỏ file và giao cho agent nhỏ (model haiku) dịch song song ra `{key: tiếng Việt}`.
3. `python patch.py --merge <file dịch>.json`. Lệnh này kiểm tra thẻ và cập nhật cả `en_source.json`.
4. Chạy lại bước 1, kiểm tra trong game, rồi commit và push.
5. Nếu patcher lỗi vì game đổi cấu trúc (tên file bundle hoặc assets, font chuyển chỗ): quét lại TMP_FontAsset theo `m_Script.m_ClassName == "TMP_FontAsset"` trên mọi `*.assets`, `level*` và `*.bundle`, rồi cập nhật `TARGETS` trong `patch.py`.

## Quy tắc dịch
- Giữ nguyên `{0}`, `{name}`, `%s`, `\n` và mọi thẻ `<...>` (`<br>`, `<waitfor=..>`, `<color=..>`, `<#ABA291>`, `<sprite ..>`).
- Giữ nguyên tên riêng: Samreignia, Abberlore, Inverland, Sarranga, Heffalump, Shankhar, Snoot, Nayana, Lords in Black...
- Bảng thuật ngữ:

| Tiếng Anh | Tiếng Việt |
|---|---|
| Lord | Lãnh chúa |
| My Lord | Thưa Lãnh chúa |
| Peasant | Nông dân |
| Rebels | Quân nổi loạn |
| Castle | Lâu đài |
| Citadel | Thành trì |
| Townhall | Tòa Thị Chính |
| Gold | Vàng |
| Wood | Gỗ |
| Stone | Đá |
| Food | Lương thực |
| Iron | Sắt |
| Soldier | Binh lính |
| Archer | Cung thủ |
| Swordsman | Kiếm sĩ |
| Spearman | **Lính giáo** (không dùng "Thương binh") |
| Undead | Tử linh |
| Mission | Nhiệm vụ |
| Settings | Cài đặt |
| Your Grace | Bệ hạ |
