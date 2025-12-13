# OCR for Unknown/Unsupported Languages

If you're trying to extract text from an image in a language that Tesseract doesn't officially support (like many local African languages), here are several strategies to improve results:

## Quick Solutions

### 1. Use Auto Mode (No Language Specification)

Try OCR without specifying a language. Tesseract will use its default character recognition:

**API:**
```bash
# Use empty string or 'auto' for lang parameter
curl -X POST "http://localhost:8080/ocr?lang=&preprocess=true" \
  -F "file=@your_image.png"
```

**Python:**
```python
import requests

with open('image.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/ocr',
        files={'file': f},
        params={'lang': '', 'preprocess': 'true'}  # Empty lang = auto mode
    )
    print(response.json()['text'])
```

### 2. Enable Image Preprocessing

Image preprocessing can significantly improve OCR accuracy for unknown languages:

**API:**
```bash
curl -X POST "http://localhost:8080/ocr?lang=&preprocess=true" \
  -F "file=@your_image.png"
```

**What preprocessing does:**
- Converts to grayscale
- Enhances contrast (1.5x)
- Enhances sharpness (2x)
- Applies noise reduction

### 3. Try Different Page Segmentation Modes (PSM)

Different PSM modes work better for different text layouts:

**Common PSM modes:**
- `6` - Uniform block of text (default, good for paragraphs)
- `7` - Single text line (good for single lines)
- `8` - Single word (good for isolated words)
- `13` - Raw line (treats image as single text line)

**Example:**
```bash
curl -X POST "http://localhost:8080/ocr?lang=&preprocess=true&psm=7" \
  -F "file=@your_image.png"
```

### 4. Try Related Languages

If your language uses a similar script/alphabet to a supported language, try that:

**Examples:**
- If your language uses Latin script → try `eng`, `fra`, `spa`, `deu`
- If your language uses Arabic script → try `ara`
- If your language uses Cyrillic → try `rus`, `ukr`

**Multi-language mode:**
```bash
# Try multiple related languages
curl -X POST "http://localhost:8080/ocr?lang=eng+fra+spa&preprocess=true" \
  -F "file=@your_image.png"
```

## Complete Example for Unknown Languages

```python
import requests

def ocr_unknown_language(image_path):
    """Try OCR with multiple strategies for unknown languages."""
    
    strategies = [
        # Strategy 1: Auto mode with preprocessing
        {'lang': '', 'preprocess': True, 'psm': 6},
        # Strategy 2: Auto mode, single line
        {'lang': '', 'preprocess': True, 'psm': 7},
        # Strategy 3: Try related languages (if Latin script)
        {'lang': 'eng+fra+spa', 'preprocess': True, 'psm': 6},
        # Strategy 4: Auto mode, raw line
        {'lang': '', 'preprocess': True, 'psm': 13},
    ]
    
    best_result = None
    best_confidence = 0
    
    with open(image_path, 'rb') as f:
        for i, strategy in enumerate(strategies, 1):
            print(f"\nTrying strategy {i}...")
            response = requests.post(
                'http://localhost:8080/ocr/detailed',
                files={'file': f},
                params=strategy
            )
            f.seek(0)  # Reset file pointer
            
            result = response.json()
            if result['success']:
                confidence = result.get('average_confidence', 0)
                print(f"  Confidence: {confidence}%")
                print(f"  Text: {result['text'][:100]}...")
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_result = result
    
    return best_result

# Use it
result = ocr_unknown_language('your_image.png')
print(f"\nBest result (confidence: {result['average_confidence']}%):")
print(result['text'])
```

## Image Quality Tips

Before using OCR, improve your image quality:

1. **High Resolution**: Use at least 300 DPI
2. **Good Contrast**: Text should be clearly visible
3. **Clean Background**: Remove noise and artifacts
4. **Straight Text**: Rotate image if text is tilted
5. **Proper Lighting**: Avoid shadows and glare

## Advanced: Training Custom Tesseract Models

For best results with unsupported languages, you can train a custom Tesseract model:

1. **Collect Training Data**: Gather 100+ images with text in your language
2. **Use Tesseract Training Tools**: 
   - `tesstrain` (Tesseract training script)
   - `jTessBoxEditor` (GUI tool for training)
3. **Create Language Data File**: Generate `.traineddata` file
4. **Install Custom Language**: Place `.traineddata` in Tesseract's `tessdata` folder

**Resources:**
- Tesseract Training Guide: https://tesseract-ocr.github.io/tessdoc/TrainingTesseract.html
- tesstrain: https://github.com/tesseract-ocr/tesstrain

## API Parameters Summary

| Parameter | Values | Description |
|-----------|--------|-------------|
| `lang` | `''` or `'auto'` | Auto mode (no language) |
| `lang` | `'eng'`, `'spa'`, etc. | Specific language |
| `lang` | `'eng+spa+fra'` | Multiple languages |
| `preprocess` | `true`/`false` | Enable image enhancement |
| `psm` | `0-13` | Page segmentation mode |

## Troubleshooting

**Problem**: Still getting poor results
- **Solution**: Try preprocessing + different PSM modes
- **Solution**: Improve image quality (higher resolution, better contrast)
- **Solution**: Consider training a custom model for your language

**Problem**: Getting empty results
- **Solution**: Check image quality and resolution
- **Solution**: Try PSM mode 7 or 13 (single line modes)
- **Solution**: Verify image contains actual text (not handwriting)

**Problem**: Wrong characters detected
- **Solution**: This is expected for unsupported languages
- **Solution**: Try related languages with similar scripts
- **Solution**: Train custom model for best accuracy

## Example cURL Commands

```bash
# Best for unknown languages - auto mode with preprocessing
curl -X POST "http://localhost:8080/ocr?lang=&preprocess=true&psm=6" \
  -F "file=@image.png"

# Single line text
curl -X POST "http://localhost:8080/ocr?lang=&preprocess=true&psm=7" \
  -F "file=@image.png"

# Detailed results with confidence scores
curl -X POST "http://localhost:8080/ocr/detailed?lang=&preprocess=true&psm=6" \
  -F "file=@image.png"
```

Remember: For unsupported languages, results may vary. The best approach is often preprocessing + trying different PSM modes, or training a custom Tesseract model for your specific language.

