# PDF Compressor CLI

Công cụ dòng lệnh (CLI) bằng Python giúp **nén file PDF nặng (1GB+)** xuống kích thước đủ nhỏ để các AI tools như **Claude** hoặc **ChatGPT** có thể upload và đọc được (<100MB, lý tưởng <30MB).

Tool xử lý PDF theo từng page (page-by-page) nên **không load toàn bộ file vào RAM**, phù hợp với file scan/nhiều hình ảnh chất lượng cao.

```bash
brew tap YOUR_USER/pdf-compressor
brew install pdf-compressor

pdf-compressor /path/to/big.pdf      # xong, không cần clone source
```

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

Sau khi cài xong, gõ `pdf-compressor <file>` ở bất kỳ terminal nào là chạy luôn — **không cần clone source, không cần activate venv**.

### Cách 1: Homebrew (khuyến nghị cho macOS)

```bash
brew tap YOUR_USER/pdf-compressor
brew install pdf-compressor
```

Sau khi cài, tool có sẵn trong `$PATH`:

```bash
pdf-compressor big.pdf                   # nén với preset medium
pdf-compressor big.pdf -q low -t 25      # preset low, target 25 MB
pdf-compressor                           # mở interactive shell
```

> Để chạy `--ocr`, brew cũng cài luôn `tesseract` (tự động qua `depends_on`).

### Cách 2: pipx (one-command, không cần brew tap)

```bash
pipx install git+https://github.com/YOUR_USER/pdf-compressor.git
```

`pipx` tự tạo venv cô lập cho tool và expose command `pdf-compressor` ra `$PATH`.

Nếu chưa có pipx: `brew install pipx && pipx ensurepath`. Để dùng OCR: `brew install tesseract`.

### Cách 3: pip

```bash
pip install git+https://github.com/YOUR_USER/pdf-compressor.git
```

### Cách 4: Clone & run từ source (cho dev)

```bash
git clone https://github.com/YOUR_USER/pdf-compressor.git
cd pdf-compressor
chmod +x setup.sh && ./setup.sh
source venv/bin/activate
pdf-compressor --help
```

`setup.sh` sẽ kiểm tra Homebrew, cài `tesseract`, tạo venv và `pip install -e .`.

---

## Sử dụng nhanh

### Interactive shell (claudekit-style REPL) — mặc định

Chạy không kèm argument → tool mở một **shell tương tác** kiểu Claude Code: gõ slash command, state giữ lại giữa các lệnh, có thể nén nhiều file liên tiếp không cần thoát:

```bash
pdf-compressor
# hoặc
pdf-compressor -I
# hoặc pre-load sẵn file:
pdf-compressor -i big.pdf -I
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
pdf-compressor --wizard
```

Tool sẽ lần lượt hỏi input/output/quality/target/pages/split/OCR/verbose rồi hiển thị bảng xác nhận → chạy → exit.

---

### Flag mode (cho power user / script)

### 1. Nén cơ bản với preset `medium` (mặc định)

```bash
pdf-compressor -i big.pdf
```

Output mặc định: `big_compressed.pdf` cùng thư mục.

### 2. Nén với preset thấp (giảm mạnh, chất lượng thấp)

```bash
pdf-compressor -i big.pdf -q low -o tiny.pdf
```

### 3. Nén để đạt đúng target size (ví dụ ~25 MB)

```bash
pdf-compressor -i big.pdf -t 25
```

Tool sẽ binary-search JPEG quality trong khoảng [10, 85] để file output có size gần target ±10%.

### 4. Chỉ xử lý một dải page

```bash
pdf-compressor -i big.pdf --pages "1-50"
pdf-compressor -i big.pdf --pages "1,3,5-10"
```

### 5. Split output thành nhiều file ≤ 30 MB

```bash
pdf-compressor -i big.pdf --split 30
```

Sẽ tạo `big_compressed_part1.pdf`, `big_compressed_part2.pdf`, …

### 6. OCR cho PDF scan

```bash
pdf-compressor -i scanned.pdf --ocr
```

Thêm text layer vô hình cho các page hiện không có text — giúp AI tool trích được nội dung.

### 7. Chi tiết quá trình xử lý

```bash
pdf-compressor -i big.pdf -v
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
├── compress_pdf.py         # CLI chính (single file, self-contained)
├── pyproject.toml          # Package metadata + entry point `pdf-compressor`
├── requirements.txt        # Python dependencies (cho setup.sh)
├── setup.sh                # Script setup dev cho macOS
├── Formula/
│   └── pdf-compressor.rb   # Homebrew formula
├── scripts/
│   └── gen_formula.py      # Regenerate formula resources từ PyPI
└── README.md               # Tài liệu (file này)
```

---

## Publish lên Homebrew (cho maintainer)

Để người khác có thể `brew install pdf-compressor`, cần một **tap repo** riêng trên GitHub:

### 1. Tag một release trên repo chính

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub sẽ tạo tarball tại `https://github.com/YOUR_USER/pdf-compressor/archive/refs/tags/v0.1.0.tar.gz`.

### 2. Tính sha256 của tarball

```bash
curl -sL https://github.com/YOUR_USER/pdf-compressor/archive/refs/tags/v0.1.0.tar.gz \
    | shasum -a 256
```

### 3. Regenerate formula với resources mới nhất từ PyPI

```bash
pip install -e .       # cài đúng versions vào env hiện tại
python scripts/gen_formula.py \
    --source-url https://github.com/YOUR_USER/pdf-compressor/archive/refs/tags/v0.1.0.tar.gz \
    --source-sha256 <sha256-từ-bước-2>
```

### 4. Tạo tap repo

Repo phải đặt tên `homebrew-<tên-tap>`. Ví dụ `homebrew-pdf-compressor`:

```bash
# Trên GitHub: tạo repo `homebrew-pdf-compressor`
git clone https://github.com/YOUR_USER/homebrew-pdf-compressor.git
cp pdf-compressor/Formula/pdf-compressor.rb homebrew-pdf-compressor/Formula/
cd homebrew-pdf-compressor
git add . && git commit -m "Initial formula" && git push
```

### 5. User cài đặt

```bash
brew tap YOUR_USER/pdf-compressor
brew install pdf-compressor
```

> **Tip**: Test local trước khi push: `brew install --build-from-source ./Formula/pdf-compressor.rb`
