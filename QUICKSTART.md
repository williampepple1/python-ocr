# Quick Start Guide - Testing the OCR API

## Step 1: Install Tesseract OCR

### Windows
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. **Important**: During installation, make sure to check "Add to PATH" or manually add to PATH
4. Or use Chocolatey: `choco install tesseract`

### macOS
```bash
brew install tesseract
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### Verify Tesseract Installation
```bash
tesseract --version
```

## Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you encounter issues, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Verify Tesseract is Accessible

Test if Python can find Tesseract:
```bash
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

If you get an error, you may need to set the Tesseract path. Edit `api.py` and add at the top (after imports):
```python
# Windows example
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Step 4: Start the API Server

### Option 1: Using the script directly
```bash
python api.py
```

### Option 2: Using uvicorn directly (recommended for development)
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8080
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 5: Test the API

### Method 1: Using the Interactive API Documentation (Easiest!)

1. Open your browser and go to: **http://localhost:8080/docs**
2. You'll see the Swagger UI with all endpoints
3. Click on any endpoint (e.g., `POST /ocr`)
4. Click "Try it out"
5. Upload an image file
6. Set the language parameter (e.g., `eng`)
7. Click "Execute"
8. See the results!

### Method 2: Using the Test Script

```bash
# First, make sure you have requests installed
pip install requests

# Test with an image
python test_api.py your_image.png
```

### Method 3: Using cURL

```bash
# Health check
curl http://localhost:8080/health

# List available languages
curl http://localhost:8080/languages

# Test OCR (replace image.png with your image file)
curl -X POST "http://localhost:8080/ocr?lang=eng" \
  -F "file=@image.png"
```

### Method 4: Using Python

Create a test file `test_ocr.py`:
```python
import requests

# Test health check
response = requests.get("http://localhost:8080/health")
print("Health:", response.json())

# Test OCR
with open('your_image.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/ocr',
        files={'file': f},
        params={'lang': 'eng'}
    )
    print("OCR Result:", response.json())
```

Run it:
```bash
python test_ocr.py
```

## Step 6: Test Command Line Tool

```bash
# Basic OCR
python ocr_tesseract.py image.png

# With language
python ocr_tesseract.py image.png -l spa

# Save to file
python ocr_tesseract.py image.png -o output.txt

# Detailed information
python ocr_tesseract.py image.png --detailed
```

## Troubleshooting

### Error: "TesseractNotFoundError"
- Make sure Tesseract is installed
- Check if it's in your PATH: `tesseract --version`
- If not in PATH, set the path in `api.py` (see Step 3)

### Error: "Language not found"
- Check available languages: `tesseract --list-langs`
- Or use the API: `curl http://localhost:8080/languages`
- Install language packs if needed

### Port 8080 already in use
- Change the port in `api.py`: `uvicorn.run(app, host="0.0.0.0", port=8001)`
- Or use: `uvicorn api:app --port 8001`

### Import errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Try upgrading pip: `pip install --upgrade pip`

## Quick Test Checklist

- [ ] Tesseract installed and accessible
- [ ] Python dependencies installed
- [ ] API server running on http://localhost:8080
- [ ] Can access http://localhost:8080/docs
- [ ] Health check returns "healthy"
- [ ] Can upload and process an image via API
- [ ] Command line tool works

## Next Steps

- Try different languages
- Test with multi-language OCR: `lang=eng+spa+fra`
- Test with different image formats
- Check the detailed OCR endpoint for confidence scores

