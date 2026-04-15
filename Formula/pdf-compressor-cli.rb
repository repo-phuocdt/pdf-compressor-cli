class PdfCompressorCli < Formula
  include Language::Python::Virtualenv

  desc "Compress large PDFs to an AI-friendly size (page-by-page, memory efficient)"
  homepage "https://github.com/repo-phuocdt/pdf-compressor-cli"
  url "https://github.com/repo-phuocdt/pdf-compressor-cli/archive/51789a14e07bef71470c20d45640b71165031d14.tar.gz"
  version "0.1.0"
  sha256 "757758f40979dbbb2f27bea8e26b483913266d9cf5f067ed994f782304701903"
  license "MIT"
  head "https://github.com/repo-phuocdt/pdf-compressor-cli.git", branch: "master"

  depends_on "python@3.12"
  depends_on "tesseract" => :recommended # needed only for --ocr

  resource "PyMuPDF" do
    url "https://files.pythonhosted.org/packages/f1/32/f6b645c51d79a188a4844140c5dabca7b487ad56c4be69c4bc782d0d11a9/pymupdf-1.27.2.2.tar.gz"
    sha256 "ea8fdc3ab6671ca98f629d5ec3032d662c8cf1796b146996b7ad306ac7ed3335"
  end
  resource "pillow" do
    url "https://files.pythonhosted.org/packages/8c/21/c2bcdd5906101a30244eaffc1b6e6ce71a31bd0742a01eb89e660ebfac2d/pillow-12.2.0.tar.gz"
    sha256 "a830b1a40919539d07806aa58e1b114df53ddd43213d9c8b75847eee6c0182b5"
  end
  resource "click" do
    url "https://files.pythonhosted.org/packages/57/75/31212c6bf2503fdf920d87fee5d7a86a2e3bcf444984126f13d8e4016804/click-8.3.2.tar.gz"
    sha256 "14162b8b3b3550a7d479eafa77dfd3c38d9dc8951f6f69c78913a8f9a7540fd5"
  end
  resource "rich" do
    url "https://files.pythonhosted.org/packages/c0/8f/0722ca900cc807c13a6a0c696dacf35430f72e0ec571c4275d2371fca3e9/rich-15.0.0.tar.gz"
    sha256 "edd07a4824c6b40189fb7ac9bc4c52536e9780fbbfbddf6f1e2502c31b068c36"
  end
  resource "pytesseract" do
    url "https://files.pythonhosted.org/packages/9f/a6/7d679b83c285974a7cb94d739b461fa7e7a9b17a3abfd7bf6cbc5c2394b0/pytesseract-0.3.13.tar.gz"
    sha256 "4bf5f880c99406f52a3cfc2633e42d9dc67615e69d8a509d74867d3baddb5db9"
  end
  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/5b/f5/4ec618ed16cc4f8fb3b701563655a69816155e79e24a17b651541804721d/markdown_it_py-4.0.0.tar.gz"
    sha256 "cb0a2b4aa34f932c007117b194e945bd74e0ec24133ceb5bac59009cda1cb9f3"
  end
  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/d6/54/cfe61301667036ec958cb99bd3efefba235e65cdeb9c84d24a8293ba1d90/mdurl-0.1.2.tar.gz"
    sha256 "bb413d29f5eea38f31dd4754dd7377d4465116fb207585f97bf925588687c1ba"
  end
  resource "Pygments" do
    url "https://files.pythonhosted.org/packages/c3/b2/bc9c9196916376152d655522fdcebac55e66de6603a76a02bca1b6414f6c/pygments-2.20.0.tar.gz"
    sha256 "6757cd03768053ff99f3039c1a36d6c0aa0b263438fcab17520b30a303a82b5f"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "pdf-compressor, version", shell_output("#{bin}/pdf-compressor --version")
  end
end
