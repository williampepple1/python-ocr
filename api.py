"""
FastAPI application for OCR (Optical Character Recognition) using Tesseract
Provides REST API endpoints for text extraction from images
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image
import io
from typing import Optional
import uvicorn
import sys

# Ensure UTF-8 encoding for stdout/stderr
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

app = FastAPI(
    title="OCR API with Tesseract",
    description="REST API for Optical Character Recognition using Tesseract OCR. Full UTF-8 and Unicode support for 100+ languages.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_text_from_image_bytes(image_bytes: bytes, lang: str = 'eng') -> str:
    """
    Extract text from image bytes using Tesseract OCR.
    Full UTF-8 and Unicode support for any language Tesseract supports.
    
    Args:
        image_bytes (bytes): Image file as bytes
        lang (str): Language code(s) for OCR (default: 'eng')
                    Can be single language like 'eng' or multiple like 'eng+spa+fra'
    
    Returns:
        str: Extracted text from the image (UTF-8 encoded)
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Extract text using pytesseract with UTF-8 support
        # pytesseract returns Unicode strings by default in Python 3
        text = pytesseract.image_to_string(image, lang=lang)
        
        # Ensure text is properly decoded (should already be Unicode string)
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        
        return text
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


def extract_text_with_details_bytes(image_bytes: bytes, lang: str = 'eng') -> dict:
    """
    Extract text with detailed information (bounding boxes, confidence scores).
    Full UTF-8 and Unicode support for any language Tesseract supports.
    
    Args:
        image_bytes (bytes): Image file as bytes
        lang (str): Language code(s) for OCR (default: 'eng')
                    Can be single language like 'eng' or multiple like 'eng+spa+fra'
    
    Returns:
        dict: Dictionary containing text and detailed data (all text UTF-8 encoded)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Get detailed data
        data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        
        # Get text with bounding boxes
        boxes = pytesseract.image_to_boxes(image, lang=lang)
        
        # Get text (Unicode string)
        text = pytesseract.image_to_string(image, lang=lang)
        
        # Ensure text is properly decoded
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        
        # Ensure boxes text is properly decoded
        if isinstance(boxes, bytes):
            boxes = boxes.decode('utf-8')
        
        # Calculate statistics
        words = [w for w in data['text'] if w.strip()]
        confidences = [int(c) for c in data['conf'] if c != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': text,
            'word_count': len(words),
            'average_confidence': round(avg_confidence, 2),
            'data': data,
            'boxes': boxes.split('\n') if boxes else []
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "OCR API with Tesseract",
        "version": "1.0.0",
        "features": {
            "utf8_support": True,
            "unicode_support": True,
            "multi_language": True,
            "supported_languages": "100+ languages"
        },
        "endpoints": {
            "POST /ocr": "Extract text from image (UTF-8/Unicode supported)",
            "POST /ocr/detailed": "Extract text with detailed information (UTF-8/Unicode supported)",
            "GET /health": "Health check",
            "GET /languages": "List available Tesseract languages"
        },
        "encoding": "UTF-8"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Try to get Tesseract version to verify it's working
        version = pytesseract.get_tesseract_version()
        return {
            "status": "healthy",
            "tesseract_version": version
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/languages")
async def get_languages():
    """Get list of available Tesseract languages."""
    try:
        languages = pytesseract.get_languages()
        return {
            "languages": languages,
            "count": len(languages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting languages: {str(e)}")


@app.post("/ocr")
async def ocr_extract_text(
    file: UploadFile = File(..., description="Image file to process"),
    lang: str = Query(
        default='eng', 
        description="Language code(s) for OCR. Single: 'eng', 'spa', 'chi_sim', 'jpn', etc. Multiple: 'eng+spa+fra'. Supports 100+ languages with full UTF-8/Unicode support."
    )
):
    """
    Extract text from an uploaded image with full UTF-8 and Unicode support.
    
    Supports any language that Tesseract supports, including:
    - European languages: English, Spanish, French, German, Italian, etc.
    - Asian languages: Chinese (Simplified/Traditional), Japanese, Korean, Thai, etc.
    - Middle Eastern: Arabic, Hebrew, Persian, etc.
    - And 100+ more languages
    
    - **file**: Image file (PNG, JPG, JPEG, TIFF, BMP, etc.)
    - **lang**: Language code(s) (default: 'eng')
                - Single: 'eng', 'spa', 'chi_sim', 'jpn', 'kor', 'ara', etc.
                - Multiple: 'eng+spa+fra' (combine languages with '+')
    
    Returns the extracted text as UTF-8 encoded string. All Unicode characters are supported.
    """
    try:
        # Read image file
        image_bytes = await file.read()
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Extract text (returns Unicode string)
        text = extract_text_from_image_bytes(image_bytes, lang)
        
        # FastAPI automatically handles UTF-8 encoding in JSON responses
        response = JSONResponse(
            content={
                "success": True,
                "text": text,
                "language": lang,
                "filename": file.filename,
                "encoding": "UTF-8"
            }
        )
        # Explicitly set UTF-8 charset in response header
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/ocr/detailed")
async def ocr_extract_detailed(
    file: UploadFile = File(..., description="Image file to process"),
    lang: str = Query(
        default='eng',
        description="Language code(s) for OCR. Single: 'eng', 'spa', 'chi_sim', 'jpn', etc. Multiple: 'eng+spa+fra'. Supports 100+ languages with full UTF-8/Unicode support."
    )
):
    """
    Extract text with detailed information from an uploaded image.
    Full UTF-8 and Unicode support for any language Tesseract supports.
    
    Supports any language that Tesseract supports, including:
    - European languages: English, Spanish, French, German, Italian, etc.
    - Asian languages: Chinese (Simplified/Traditional), Japanese, Korean, Thai, etc.
    - Middle Eastern: Arabic, Hebrew, Persian, etc.
    - And 100+ more languages
    
    - **file**: Image file (PNG, JPG, JPEG, TIFF, BMP, etc.)
    - **lang**: Language code(s) (default: 'eng')
                - Single: 'eng', 'spa', 'chi_sim', 'jpn', 'kor', 'ara', etc.
                - Multiple: 'eng+spa+fra' (combine languages with '+')
    
    Returns extracted text along with confidence scores, word count, and bounding boxes.
    All text is UTF-8 encoded and supports full Unicode character sets.
    """
    try:
        # Read image file
        image_bytes = await file.read()
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Extract text with details (returns Unicode strings)
        result = extract_text_with_details_bytes(image_bytes, lang)
        
        # FastAPI automatically handles UTF-8 encoding in JSON responses
        response = JSONResponse(
            content={
                "success": True,
                "text": result['text'],
                "word_count": result['word_count'],
                "average_confidence": result['average_confidence'],
                "language": lang,
                "filename": file.filename,
                "encoding": "UTF-8",
                "data": result['data'],
                "boxes": result['boxes']
            }
        )
        # Explicitly set UTF-8 charset in response header
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

