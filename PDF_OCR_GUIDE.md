# PDF OCR Guide

This guide explains how to extract text from PDFs that contain embedded images or scanned content.

## Overview

The PDF OCR feature **extracts embedded images directly from the PDF** and then runs OCR on each extracted image. This is perfect for:
- Scanned PDFs with embedded images
- PDFs with embedded images containing text
- Image-based PDFs
- PDFs where text cannot be directly extracted

**Important**: This feature extracts the actual image objects embedded in the PDF (not converting pages to images). It works with JPEG, PNG, and other image formats embedded within the PDF structure.

## Prerequisites

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install `PyPDF2` which is used to extract embedded images from PDFs.

**Note**: You do NOT need poppler-utils for this feature. We extract images directly from the PDF structure.

## API Endpoints

### 1. POST `/ocr/pdf` - Basic PDF OCR

Extract text from all pages of a PDF.

**Request:**
- Method: `POST`
- URL: `http://localhost:8080/ocr/pdf`
- Content-Type: `multipart/form-data`
- Parameters:
  - `file` (required): PDF file
  - `lang` (optional): Language code (default: `'eng'`)
  - `preprocess` (optional): Enable preprocessing (default: `false`)
  - `psm` (optional): Page Segmentation Mode (0-13)
  - `first_page` (optional): First page to process (1-indexed)
  - `last_page` (optional): Last page to process (1-indexed)

**Response:**
```json
{
  "success": true,
  "text": "All text combined without page markers...",
  "combined_text": "--- Page 1 ---\nText from page 1...\n\n--- Page 2 ---\nText from page 2...",
  "total_pages": 5,
  "pages_processed": 5,
  "total_words": 1234,
  "average_confidence": 95.5,
  "language": "eng",
  "filename": "document.pdf",
  "encoding": "UTF-8",
  "preprocessed": false,
  "psm_mode": null,
  "pages": [
    {
      "page": 1,
      "text": "Text from page 1...",
      "text_length": 250
    },
    {
      "page": 2,
      "text": "Text from page 2...",
      "text_length": 300
    }
  ],
  "pages_data": [
    {
      "page": 1,
      "word_count": 45,
      "average_confidence": 96.2
    }
  ]
}
```

### 2. POST `/ocr/pdf/detailed` - Detailed PDF OCR

Extract text with detailed information (confidence scores, bounding boxes) for each page.

**Request:** Same as `/ocr/pdf` but returns more detailed information per page.

**Response:** Includes detailed OCR data for each page with bounding boxes and confidence scores.

## Usage Examples

### Using cURL

**Basic PDF OCR:**
```bash
curl -X POST "http://localhost:8080/ocr/pdf?lang=eng&preprocess=true" \
  -F "file=@document.pdf"
```

**PDF OCR with page range:**
```bash
# Process only pages 2-5
curl -X POST "http://localhost:8080/ocr/pdf?lang=eng&first_page=2&last_page=5" \
  -F "file=@document.pdf"
```

**PDF OCR for unknown language:**
```bash
curl -X POST "http://localhost:8080/ocr/pdf?lang=&preprocess=true&psm=6" \
  -F "file=@document.pdf"
```

### Using Python

```python
import requests

# Basic PDF OCR
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/ocr/pdf',
        files={'file': f},
        params={
            'lang': 'eng',
            'preprocess': 'true'
        }
    )
    result = response.json()
    print(f"Total pages: {result['total_pages']}")
    print(f"Total words: {result['total_words']}")
    print(f"Text:\n{result['text']}")

# PDF OCR with page range
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/ocr/pdf',
        files={'file': f},
        params={
            'lang': 'eng',
            'preprocess': 'true',
            'first_page': 1,
            'last_page': 3  # Process only first 3 pages
        }
    )
    result = response.json()
    print(f"Processed {result['pages_processed']} pages")
    
    # Access text per page
    for page in result['pages']:
        print(f"\nPage {page['page']}:")
        print(page['text'])

# Detailed PDF OCR
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/ocr/pdf/detailed',
        files={'file': f},
        params={
            'lang': 'eng',
            'preprocess': 'true'
        }
    )
    result = response.json()
    
    # Access detailed info per page
    for page in result['pages']:
        print(f"\nPage {page['page']}:")
        print(f"  Text: {page['text'][:100]}...")
        print(f"  Word Count: {page['word_count']}")
        print(f"  Confidence: {page['average_confidence']}%")
```

### Using JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8080/ocr/pdf?lang=eng&preprocess=true', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log(`Total pages: ${data.total_pages}`);
  console.log(`Total words: ${data.total_words}`);
  console.log(`Text: ${data.text}`);
  
  // Access per-page data
  data.pages.forEach(page => {
    console.log(`Page ${page.page}: ${page.text}`);
  });
});
```

## Parameters Explained

### `lang` (Language)
- **Default**: `'eng'`
- **Options**: 
  - Single language: `'eng'`, `'spa'`, `'chi_sim'`, `'jpn'`, etc.
  - Multiple languages: `'eng+spa+fra'`
  - Auto mode: `''` or `'auto'` (for unknown languages)

### `preprocess` (Image Preprocessing)
- **Default**: `false`
- **When to use**: 
  - Low-quality PDFs
  - Scanned documents
  - Unknown languages
- **What it does**: Enhances contrast, sharpness, and applies noise reduction

### `psm` (Page Segmentation Mode)
- **Default**: `null` (auto)
- **Common values**:
  - `6`: Uniform block of text (good for paragraphs)
  - `7`: Single text line
  - `8`: Single word
  - `13`: Raw line

### `first_page` and `last_page` (Page Range)
- **Default**: `null` (process all pages)
- **Use case**: Process specific pages only
- **Example**: `first_page=2&last_page=5` processes pages 2, 3, 4, and 5

## Best Practices

1. **For Scanned PDFs**: Always use `preprocess=true`
   ```bash
   curl -X POST "http://localhost:8080/ocr/pdf?preprocess=true" \
     -F "file=@scanned.pdf"
   ```

2. **For Unknown Languages**: Use auto mode with preprocessing
   ```bash
   curl -X POST "http://localhost:8080/ocr/pdf?lang=&preprocess=true&psm=6" \
     -F "file=@document.pdf"
   ```

3. **For Large PDFs**: Process in batches using page ranges
   ```python
   # Process 10 pages at a time
   for start in range(1, total_pages + 1, 10):
       end = min(start + 9, total_pages)
       # Process pages start to end
   ```

4. **For Better Accuracy**: 
   - Use higher DPI (currently 300 DPI)
   - Enable preprocessing
   - Choose appropriate PSM mode
   - Use correct language code

## Troubleshooting

### Error: "No images found in PDF"

**Problem**: PDF doesn't contain embedded images, or images are in an unsupported format.

**Solutions**:
- Verify PDF contains embedded images (not just text)
- Check if PDF is actually image-based (scanned document)
- Some PDFs may have images in formats we can't extract - try a different PDF tool if needed

### Error: "Empty text extracted"

**Problem**: PDF pages don't contain readable text or OCR failed.

**Solutions**:
1. Enable preprocessing: `preprocess=true`
2. Try different PSM mode: `psm=7` or `psm=13`
3. Use auto language mode: `lang=`
4. Check PDF quality - ensure text is clear and readable

### Error: "Memory error" or "Slow processing"

**Problem**: PDF is too large or has too many pages.

**Solutions**:
1. Process pages in batches using `first_page` and `last_page`
2. Reduce DPI (modify code if needed, default is 300)
3. Process fewer pages at a time

### Poor OCR Accuracy

**Solutions**:
1. Enable preprocessing: `preprocess=true`
2. Use correct language: `lang=eng` (or your language)
3. Try different PSM modes
4. Ensure PDF has good quality images (at least 300 DPI)

## Performance Notes

- **Processing Time**: ~1-3 seconds per image (depending on image size and complexity)
- **Memory Usage**: Depends on embedded image sizes
- **Image Quality**: Uses original embedded image quality (no conversion, preserves quality)

## Limitations

1. **Text-based PDFs**: If PDF already has selectable text, use a PDF text extractor instead (faster)
2. **PDFs without embedded images**: If PDF doesn't contain embedded images, this won't work. PDF must have image objects embedded in it.
3. **Image format support**: Supports JPEG, PNG, and most common embedded image formats. Some proprietary formats may not be extractable.
4. **Large PDFs**: Very large PDFs (>100 pages) may take significant time
5. **Handwriting**: OCR works best with printed text, not handwriting
6. **Complex Layouts**: May struggle with complex multi-column layouts

## Example Use Cases

1. **Scanned Documents**: Convert scanned PDFs to searchable text
2. **Image-based PDFs**: Extract text from PDFs with embedded images
3. **Multi-language PDFs**: Process PDFs with text in multiple languages
4. **Batch Processing**: Process multiple PDFs programmatically
5. **Document Digitization**: Convert physical documents (scanned to PDF) to digital text

## Next Steps

- Try the interactive API docs: http://localhost:8080/docs
- Test with your PDF files
- Adjust parameters based on your needs
- See `UNKNOWN_LANGUAGES.md` for handling unsupported languages

