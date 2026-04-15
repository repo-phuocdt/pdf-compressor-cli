# PDF Compressor CLI

Công cụ dòng lệnh (CLI) bằng Python giúp **nén file PDF nặng (1GB+)** xuống kích thước đủ nhỏ để các AI tools như **Claude** hoặc **ChatGPT** có thể upload và đọc được (<100MB, lý tưởng <30MB).

Tool xử lý PDF theo từng page (page-by-page) nên **không load toàn bộ file vào RAM**, phù hợp với file scan/nhiều hình ảnh chất lượng cao.

---

## Tính năng

- **Interactive mode**: chạy không có argument → hỏi từng option theo kiểu wizard (giống Claude Code)
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

### Interactive mode (khuyến nghị cho người mới)

Chạy không có argument hoặc với `-I`, tool sẽ hỏi từng option một:

```bash
python compress_pdf.py
# hoặc
python compress_pdf.py -I
```

Tool sẽ lần lượt hỏi:

1. **Input PDF path** — đường dẫn file PDF (hỗ trợ `~`, env vars, kéo-thả)
2. **Output path** — mặc định `{name}_compressed.pdf`
3. **Quality preset** — `low` / `medium` / `high`
4. **Target size (MB)?** — y/n, nếu có thì nhập số MB
5. **Override DPI?** — y/n, nếu có thì nhập DPI tùy chỉnh
6. **Page range?** — y/n, nếu có thì nhập `"1-50"` / `"1,3,5-10"`
7. **Split output?** — y/n, nếu có thì nhập MB mỗi chunk
8. **OCR?** — y/n
9. **Verbose?** — y/n

Sau đó hiển thị bảng tóm tắt và hỏi **Proceed?** để xác nhận. Có thể Ctrl+C để hủy bất cứ lúc nào.

> Tip: nếu đã biết input file, chạy `python compress_pdf.py -i big.pdf -I` để tool skip câu hỏi đầu và hỏi các option còn lại.

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
| `-i, --input FILE` | File PDF đầu vào. Nếu bỏ qua sẽ tự vào interactive mode |
| `-I, --interactive` | Bắt buộc vào interactive mode (hỏi từng option) |
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
