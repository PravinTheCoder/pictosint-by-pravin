# Installation Guide

## 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/pictosint_by_pravin.git
cd pictosint_by_pravin
```

## 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Install Tesseract

### Kali / Debian / Ubuntu

```bash
sudo apt update
sudo apt install -y tesseract-ocr
```

Verify:

```bash
tesseract --version
```

## 5. Verify Python

```bash
python3 --version
python3 -c "import PIL, pytesseract, requests, numpy; print('Python dependencies OK')"
```

## 6. Add the application

Place the current PICTOSINT engine in the repository root, for example:

```text
pictosint_by_pravin/
├── pictosint_geo.py
├── requirements.txt
└── ...
```

## 7. Run

```bash
python3 pictosint_geo.py /path/to/image.jpg
```

## Troubleshooting

### `ModuleNotFoundError`

Activate the virtual environment and reinstall:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Tesseract not found

```bash
which tesseract
tesseract --version
```

If nothing is returned:

```bash
sudo apt install -y tesseract-ocr
```

### No useful OCR

The source image may be too small, blurred, compressed, rotated, or contain little text. OCR should be treated as a clue-generation stage, not as ground truth.

### No satellite candidates

Check that the candidate-generation/geocoding stage produced valid latitude/longitude pairs and that the machine has network access.
