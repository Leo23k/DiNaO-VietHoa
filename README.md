# Diplomacy is Not an Option – Bản Việt hoá

Bản Việt hoá không chính thức cho **Diplomacy is Not an Option**, kèm font **Patrick Hand** có đủ dấu tiếng Việt.

Repo **không chứa file nào của game**. Patcher chỉ sửa bản game bạn đã có trên máy.

## Nội dung
- Dịch toàn bộ 7.668 dòng: cắt cảnh, nhiệm vụ, giao diện, công trình, đơn vị, nghiên cứu, gợi ý, hướng dẫn.
- Toàn bộ font chữ Latin trong game (TextMeshPro và font thường) được thay bằng Patrick Hand.

## Cài đặt
1. Cài [Python 3.10+](https://www.python.org/downloads/), nhớ tick **Add Python to PATH**.
2. Tải repo này về (Code → Download ZIP) và giải nén.
3. Chạy `CaiDat.bat`, kéo thả thư mục game (thư mục có file `Diplomacy is Not an Option.exe`) vào cửa sổ, rồi bấm Enter.
4. Đợi vài phút. Vào game: **Settings → Language → English**.

Hoặc chạy bằng dòng lệnh:
```
pip install -r requirements.txt
python patch.py "D:\duong\dan\Diplomacy is Not an Option"
```

## Gỡ bỏ
Chạy `KhoiPhuc.bat`, hoặc `python patch.py "<thư mục game>" --restore`. File gốc được sao lưu trong thư mục `_backup_viethoa` cạnh game.

## Lưu ý
- Bản Việt hoá **ghi đè lên tiếng Anh**.
- Patrick Hand không có chữ Nga. Sau khi patch, tiếng Nga sẽ lỗi font; tiếng Trung/Nhật/Hàn vẫn giữ font gốc.
- Khi game cập nhật, chỉ cần chạy lại `CaiDat.bat`. Patcher tự nhận ra file gốc mới và sao lưu lại. Những dòng chữ mới hoặc bị sửa sẽ tạm hiện tiếng Anh và được liệt kê trong `can_dich.json`.

## Cập nhật bản dịch (cho người đóng góp)
1. Chạy patcher. Các dòng chưa dịch sẽ được ghi ra `can_dich.json`, dạng `{key: tiếng Anh}`.
2. Dịch các dòng đó ra một file mới, ví dụ `moi.json`, dạng `{key: tiếng Việt}`, giữ nguyên các thẻ `<...>` và `{0}`.
3. Chạy `python patch.py --merge moi.json` để gộp vào `data/vi.json`. Dòng nào có thẻ không khớp sẽ bị bỏ qua.
4. Chạy lại patcher để áp dụng.
- Đã thử với bản game dùng Unity 2021.3.45f2.

## Bản quyền
- Game © Door 407. Đây là bản dịch do người hâm mộ làm, không liên quan tới nhà phát hành.
- Font Patrick Hand © Patrick Wagesreiter, phát hành theo SIL Open Font License 1.1 (xem `data/OFL.txt`).
- Góp ý bản dịch: mở Issue hoặc Pull Request sửa `data/vi.json`.
