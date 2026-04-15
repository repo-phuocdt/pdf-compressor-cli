# PDF Compressor CLI

Công cụ dòng lệnh (CLI) bằng Python giúp **nén file PDF nặng (1GB+)** xuống kích thước đủ nhỏ để các AI tools như **Claude** hoặc **ChatGPT** có thể upload và đọc được (<100MB, lý tưởng <30MB).

Tool xử lý PDF theo từng page (page-by-page) nên **không load toàn bộ file vào RAM**, phù hợp với file scan/nhiều hình ảnh chất lượng cao.

---

## Tính năng

- **Interactive shell**: chạy không có argument → mở REPL kiểu Claude Code với slash commands (`/preset`, `/target`, `/compress`, …), state giữ lại giữa các lệnh, nén nhiều file trong một session
- **Wizard mode** (`--wizard`): hỏi từng option một rồi chạy một lần
- Nén ảnh trong PDF (giảm DPI + re-encode JPEG) theo 3 preset: `low` / `medium` / `high`
- Tự động binary search quality để đạt **target size** theo MB
- Chọn **page range** (ví dụ `1-50` hoặc `1,3,5-10`)
- **Split** output thành nhiều file nhỏ theo dung lượng
- Tuỳ chọn **OCR** cho PDF scan (thêm text layer vô hình)
- Progress bar đẹp + summary chi tiết
- Strip metadata, garbage collect để giảm size tối đa
- Handle Ctrl+C → cleanup file tạm
- Handle PDF bị mã hoá (encrypted) → báo lỗi rõ ràng

---

## Yêu cầu

- **macOS** (Apple Silicon hoặc Intel)
- **Python 3.9+**
- **Homebrew** (dùng để cài `tesseract` nếu muốn OCR)

---

## Cài đặt

```bash
cd pdf-compressor
chmod +x setup.sh
./setup.sh
```

Script `setup.sh` sẽ tự động:

1. Kiểm tra Homebrew — nếu thiếu sẽ báo lỗi và hướng dẫn cài từ https://brew.sh
2. Kiểm tra & cài `tesseract` (cho OCR) qua Homebrew nếu chưa có
3. Kiểm tra `python3`
4. Tạo virtualenv `./venv` và cài các Python package trong `requirements.txt`

Sau khi cài xong, kích hoạt venv trước khi dùng:

```bash
source venv/bin/activate
python compress_pdf.py --help
```

---

## Sử dụng nhanh

### Interactive shell (claudekit-style REPL) — mặc định

Chạy không kèm argument → tool mở một **shell tương tác** kiểu Claude Code: gõ slash command, state giữ lại giữa các lệnh, có thể nén nhiều file liên tiếp không cần thoát:

```bash
python compress_pdf.py
# hoặc
python compress_pdf.py -I
# hoặc pre-load sẵn file:
python compress_pdf.py -i big.pdf -I
```

Ví dụ một session:

```
pdf-compressor› /help                      # xem tất cả lệnh
pdf-compressor› /preset low                # đổi preset
pdf-compressor› /target 25                 # set target size 25 MB
pdf-compressor› /pages 1-50                # chỉ lấy 50 page đầu
pdf-compressor› /status                    # xem cấu hình hiện tại
pdf-compressor› big.pdf                    # chỉ paste path → compress luôn
pdf-compressor› another.pdf                # file tiếp theo, vẫn dùng setting cũ
pdf-compressor› /target off                # bỏ target, quay về preset
pdf-compressor› /exit                      # thoát
```

#### Danh sách slash command

| Lệnh | Mô tả |
| --- | --- |
| `/help`, `/?` | Hiện bảng lệnh |
| `/status`, `/show` | Hiện setting hiện tại |
| `/preset <low\|medium\|high>` | Đổi preset |
| `/target <MB> \| off` | Set target size MB |
| `/dpi <N> \| off` | Override DPI |
| `/pages <range> \| all` | Đặt page range (`"1-50"` / `"1,3,5-10"`) |
| `/split <MB> \| off` | Split output |
| `/ocr on\|off` | Bật/tắt OCR (gõ `/ocr` không tham số để toggle) |
| `/verbose on\|off` | Bật/tắt verbose |
| `/output <path> \| default` | Đặt output path |
| `/compress <path>` | Compress file với setting hiện tại |
| `<path>` | Shortcut cho `/compress <path>` (paste/drag file trực tiếp) |
| Enter (dòng trống) | Chạy lại với file đã compress gần nhất |
| `/reset` | Reset setting về mặc định |
| `/clear`, `/cls` | Clear màn hình |
| `/exit`, `/quit`, `q`, Ctrl+D | Thoát shell |

**Mẹo**: Ctrl+C ở prompt sẽ huỷ dòng đang gõ (không thoát shell). Ctrl+C khi đang compress sẽ huỷ job hiện tại và quay về shell.

---

### Wizard mode (one-shot, hỏi tuần tự rồi exit)

Nếu bạn chỉ cần chạy một lần và muốn tool hỏi từng option:

```bash
python compress_pdf.py --wizard
```

Tool sẽ lần lượt hỏi input/output/quality/target/pages/split/OCR/verbose rồi hiển thị bảng xác nhận → chạy → exit.

---

### Flag mode (cho power user / script)

### 1. Nén cơ bản với preset `medium` (mặc định)

```bash
python compress_pdf.py -i big.pdf
```

Output mặc định: `big_compressed.pdf` cùng thư mục.

### 2. Nén với preset thấp (giảm mạnh, chất lượng thấp)

```bash
python compress_pdf.py -i big.pdf -q low -o tiny.pdf
```

### 3. Nén để đạt đúng target size (ví dụ ~25 MB)

```bash
python compress_pdf.py -i big.pdf -t 25
```

Tool sẽ binary-search JPEG quality trong khoảng [10, 85] để file output có size gần target ±10%.

### 4. Chỉ xử lý một dải page

```bash
python compress_pdf.py -i big.pdf --pages "1-50"
python compress_pdf.py -i big.pdf --pages "1,3,5-10"
```

### 5. Split output thành nhiều file ≤ 30 MB

```bash
python compress_pdf.py -i big.pdf --split 30
```

Sẽ tạo `big_compressed_part1.pdf`, `big_compressed_part2.pdf`, …

### 6. OCR cho PDF scan

```bash
python compress_pdf.py -i scanned.pdf --ocr
```

Thêm text layer vô hình cho các page hiện không có text — giúp AI tool trích được nội dung.

### 7. Chi tiết quá trình xử lý

```bash
python compress_pdf.py -i big.pdf -v
```

---

## Tham số CLI

| Flag | Mô tả |
| --- | --- |
| `-i, --input FILE` | File PDF đầu vào. Nếu bỏ qua sẽ tự mở interactive shell |
| `-I, --interactive` | Bắt buộc mở interactive shell (claudekit-style REPL) |
| `--wizard` | One-shot wizard: hỏi từng option rồi exit |
| `-o, --output FILE` | File đầu ra (mặc định: `{name}_compressed.pdf`) |
| `-q, --quality TEXT` | Preset: `low` \| `medium` \| `high` (mặc định: `medium`) |
| `-t, --target-size INT` | Target size (MB). Tự binary-search quality |
| `--dpi INT` | Custom DPI (override preset) |
| `--pages TEXT` | Page range, ví dụ: `"1-50"` hoặc `"1,3,5-10"` |
| `--split INT` | Split output thành chunk tối đa N MB |
| `--ocr` | OCR scanned pages (cần `tesseract` + `pytesseract`) |
| `-v, --verbose` | In chi tiết |
| `-h, --help` | Xem help |

---

## Preset quality

| Preset | DPI | JPEG quality | Gợi ý dùng cho |
| --- | --- | --- | --- |
| `low` | 72 | 30 | Chỉ cần text/AI đọc, không quan trọng hình |
| `medium` | 150 | 50 | Cân bằng dung lượng vs chất lượng (mặc định) |
| `high` | 200 | 70 | Giữ chất lượng hình, nén nhẹ |

---

## Lưu ý

- **PDF bị mã hoá (encrypted)**: Tool sẽ báo lỗi và thoát. Bạn cần giải mã file bằng công cụ khác (ví dụ: `qpdf --decrypt input.pdf output.pdf`) trước khi dùng.
- **RAM**: Tool xử lý từng page và chỉ giữ page hiện tại trong memory, nên file 1GB không gây tràn RAM.
- **OCR**: Chạy OCR khá chậm vì phải render + nhận dạng từng page. Với file 500+ page, cân nhắc chia page range.
- **Target size**: Nếu target quá nhỏ so với mức nén tối thiểu, tool sẽ lưu file "best effort" (gần target nhất) kèm cảnh báo trong log verbose.
- **Ctrl+C**: Trong quá trình chạy, Ctrl+C sẽ cleanup các file tạm rồi exit code 130.

---

## Troubleshooting

**`tesseract: command not found` khi dùng `--ocr`**
→ Cài qua Homebrew: `brew install tesseract`

**`ModuleNotFoundError: fitz`**
→ Chưa activate venv. Chạy `source venv/bin/activate` rồi thử lại.

**Output file vẫn quá lớn**
→ Thử `-q low` hoặc kết hợp `-t 20` để force target size. Với PDF có nhiều ảnh vector hoặc font nhúng lớn, hãy cân nhắc split thêm.

---

## Cấu trúc project

```
pdf-compressor/
├── compress_pdf.py     # CLI chính (single file, self-contained)
├── requirements.txt    # Python dependencies
├── setup.sh            # Script setup cho macOS
└── README.md           # Tài liệu (file này)
```
