# Python OCR with Tesseract

A simple and powerful OCR (Optical Character Recognition) application using Tesseract OCR engine and Python.

## Features

- Extract text from images (PNG, JPG, JPEG, TIFF, BMP, etc.)
- **Full UTF-8 and Unicode support** - Extract text in any language Tesseract supports
- **100+ languages supported** - English, Spanish, Chinese, Japanese, Korean, Arabic, Hebrew, and many more
- **Multi-language OCR** - Combine multiple languages (e.g., 'eng+spa+fra')
- Save extracted text to file
- Detailed OCR information (bounding boxes, confidence scores)
- Command-line interface
- **REST API with FastAPI** - Serve OCR as web API endpoints with UTF-8 JSON responses

## Prerequisites

### 1. Install Tesseract OCR

**Windows:**
- Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Or use chocolatey: `choco install tesseract`
- After installation, add Tesseract to your PATH or set the path in the script

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**Linux (Fedora):**
```bash
sudo dnf install tesseract
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

#### Basic Usage

Extract text from an image:
```bash
python ocr_tesseract.py image.png
```

#### Save Output to File

```bash
python ocr_tesseract.py image.png -o output.txt
```

#### Use Different Language

```bash
python ocr_tesseract.py image.png -l spa  # Spanish
python ocr_tesseract.py image.png -l fra  # French
python ocr_tesseract.py image.png -l deu  # German
```

#### Get Detailed Information

```bash
python ocr_tesseract.py image.png --detailed
```

### REST API with FastAPI

#### Start the API Server

```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

#### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### API Endpoints

**1. Root Endpoint**
```bash
GET http://localhost:8000/
```
Returns API information and available endpoints.

**2. Health Check**
```bash
GET http://localhost:8000/health
```
Returns server health status and Tesseract version.

**3. List Available Languages**
```bash
GET http://localhost:8000/languages
```
Returns list of available Tesseract languages.

**4. Extract Text (Basic)**
```bash
POST http://localhost:8000/ocr
Content-Type: multipart/form-data

Form Data:
- file: [image file]
- lang: eng (optional, default: 'eng')
```

**5. Extract Text (Detailed)**
```bash
POST http://localhost:8000/ocr/detailed
Content-Type: multipart/form-data

Form Data:
- file: [image file]
- lang: eng (optional, default: 'eng')
```

#### Example API Usage

**Using cURL:**
```bash
# Basic OCR (English)
curl -X POST "http://localhost:8000/ocr?lang=eng" \
  -F "file=@image.png"

# OCR with Chinese (Simplified) - UTF-8 supported
curl -X POST "http://localhost:8000/ocr?lang=chi_sim" \
  -F "file=@chinese_image.png"

# Multi-language OCR (English + Spanish + French)
curl -X POST "http://localhost:8000/ocr?lang=eng+spa+fra" \
  -F "file=@multilingual.png"

# Detailed OCR with Japanese - Full Unicode support
curl -X POST "http://localhost:8000/ocr/detailed?lang=jpn" \
  -F "file=@japanese_image.png"
```

**Using Python requests:**
```python
import requests

# Basic OCR (English)
with open('image.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/ocr',
        files={'file': f},
        params={'lang': 'eng'}
    )
    result = response.json()
    print(result['text'])  # UTF-8 encoded text

# OCR with Chinese - Full Unicode support
with open('chinese.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/ocr',
        files={'file': f},
        params={'lang': 'chi_sim'}
    )
    result = response.json()
    print(result['text'])  # Chinese characters properly encoded in UTF-8
    print(f"Encoding: {result['encoding']}")  # Shows "UTF-8"

# Multi-language OCR
with open('multilingual.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/ocr',
        files={'file': f},
        params={'lang': 'eng+spa+fra'}  # English + Spanish + French
    )
    result = response.json()
    print(result['text'])  # Mixed language text in UTF-8

# Detailed OCR with Arabic - Full Unicode support
with open('arabic.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/ocr/detailed',
        files={'file': f},
        params={'lang': 'ara'}
    )
    result = response.json()
    print(f"Text: {result['text']}")  # Arabic text in UTF-8
    print(f"Confidence: {result['average_confidence']}%")
    print(f"Word Count: {result['word_count']}")
    print(f"Encoding: {result['encoding']}")  # UTF-8
```

**Using JavaScript (fetch):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/ocr?lang=eng', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Command Line Options

- `image_path`: Path to the image file (required)
- `-o, --output`: Output file path to save extracted text
- `-l, --lang`: Language code (default: 'eng')
- `-d, --detailed`: Show detailed OCR information

## Supported Image Formats

- PNG
- JPEG/JPG
- TIFF
- BMP
- GIF
- And other formats supported by PIL/Pillow

## Language Support & UTF-8 Encoding

### UTF-8 and Unicode Support

✅ **Full UTF-8 and Unicode support** - The API handles all Unicode characters correctly:
- All text responses are UTF-8 encoded
- JSON responses include `"encoding": "UTF-8"` field
- Response headers explicitly set `Content-Type: application/json; charset=utf-8`
- Supports emojis, special characters, and any Unicode text

### Supported Languages

Tesseract supports **100+ languages** with full Unicode support. Common language codes:

**European Languages:**
- `eng` - English
- `spa` - Spanish
- `fra` - French
- `deu` - German
- `ita` - Italian
- `por` - Portuguese
- `rus` - Russian
- `pol` - Polish
- `ukr` - Ukrainian

**Asian Languages:**
- `chi_sim` - Chinese (Simplified)
- `chi_tra` - Chinese (Traditional)
- `jpn` - Japanese
- `kor` - Korean
- `tha` - Thai
- `vie` - Vietnamese
- `hin` - Hindi

**Middle Eastern Languages:**
- `ara` - Arabic
- `heb` - Hebrew
- `fas` - Persian/Farsi
- `urd` - Urdu

**And many more!**

### Multi-Language OCR

You can combine multiple languages for better recognition of mixed-language documents:

**API Example:**
```bash
# Extract text using English + Spanish + French
curl -X POST "http://localhost:8000/ocr?lang=eng+spa+fra" \
  -F "file=@multilingual_document.png"
```

**Python Example:**
```python
import requests

with open('multilingual.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/ocr',
        files={'file': f},
        params={'lang': 'eng+spa+chi_sim'}  # English + Spanish + Chinese
    )
    result = response.json()
    print(result['text'])  # UTF-8 encoded text with all languages
```

**Command Line:**
```bash
python ocr_tesseract.py multilingual.png -l "eng+spa+fra"
```

To see all available languages on your system, run:
```bash
tesseract --list-langs
```

Or use the API endpoint:
```bash
curl http://localhost:8000/languages
```

## Troubleshooting

### Tesseract Not Found

If you get an error that Tesseract is not found, you may need to specify the path to the Tesseract executable. Add this to the top of `ocr_tesseract.py`:

```python
# Windows example
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# macOS example
pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'

# Linux example
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
```

### Language Not Found

Make sure you have installed the language data pack for Tesseract. For example, on Windows, you can download language packs from the Tesseract installer.

## Example

```bash
# Extract text from a screenshot
python ocr_tesseract.py screenshot.png

# Extract text in Spanish and save to file
python ocr_tesseract.py document.jpg -l spa -o spanish_text.txt

# Get detailed OCR analysis
python ocr_tesseract.py image.png --detailed
```

## License

This project is open source and available for use.


