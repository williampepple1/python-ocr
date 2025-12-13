"""
FastAPI application for OCR (Optical Character Recognition) using Tesseract
Provides REST API endpoints for text extraction from images
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
from typing import Optional, List
import uvicorn
import sys
import tempfile
import os
import PyPDF2
import csv

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


def preprocess_image(image: Image.Image, enhance: bool = True) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy.
    Useful for low-quality images or unknown languages.
    
    Args:
        image: PIL Image object
        enhance: Whether to apply enhancement filters
    
    Returns:
        Preprocessed PIL Image
    """
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    if enhance:
        # Convert to grayscale for better OCR
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Apply slight denoising
        image = image.filter(ImageFilter.MedianFilter(size=3))
    
    return image


def extract_text_from_image_bytes(
    image_bytes: bytes, 
    lang: str = 'eng',
    preprocess: bool = False,
    psm: Optional[int] = None
) -> str:
    """
    Extract text from image bytes using Tesseract OCR.
    Full UTF-8 and Unicode support for any language Tesseract supports.
    
    Args:
        image_bytes (bytes): Image file as bytes
        lang (str): Language code(s) for OCR (default: 'eng')
                    Can be single language like 'eng' or multiple like 'eng+spa+fra'
                    Use 'osd' for orientation/script detection, or empty string for auto
        preprocess (bool): Apply image preprocessing to improve accuracy
        psm (int): Page segmentation mode (0-13). 
                   Common: 6 (uniform block), 7 (single line), 8 (single word), 13 (raw line)
    
    Returns:
        str: Extracted text from the image (UTF-8 encoded)
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Preprocess image if requested (helpful for unknown languages)
        if preprocess:
            image = preprocess_image(image, enhance=True)
        
        # Build Tesseract config
        config = ''
        if psm is not None:
            config += f'--psm {psm} '
        
        # Handle unknown/unsupported languages
        # If lang is empty or 'auto', try without language specification
        # This uses Tesseract's default character recognition
        if lang and lang.lower() not in ['', 'auto', 'none']:
            # Extract text using pytesseract with UTF-8 support
            text = pytesseract.image_to_string(image, lang=lang, config=config.strip())
        else:
            # Try without language specification (uses default/OSD mode)
            # This can sometimes work for unknown languages
            if not config:
                config = '--psm 6'  # Uniform block of text
            text = pytesseract.image_to_string(image, config=config.strip())
        
        # Ensure text is properly decoded (should already be Unicode string)
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        
        return text
    
    except pytesseract.TesseractError as e:
        # If language not found, try without language specification
        if 'language' in str(e).lower() or 'lang' in str(e).lower():
            try:
                image = Image.open(io.BytesIO(image_bytes))
                if preprocess:
                    image = preprocess_image(image, enhance=True)
                config = f'--psm 6' if psm is None else f'--psm {psm}'
                text = pytesseract.image_to_string(image, config=config)
                if isinstance(text, bytes):
                    text = text.decode('utf-8')
                return text
            except Exception as e2:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Language '{lang}' not found. Error: {str(e)}. Tried fallback mode but failed: {str(e2)}"
                )
        raise HTTPException(status_code=400, detail=f"Tesseract error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


def extract_text_with_details_bytes(
    image_bytes: bytes, 
    lang: str = 'eng',
    preprocess: bool = False,
    psm: Optional[int] = None
) -> dict:
    """
    Extract text with detailed information (bounding boxes, confidence scores).
    Full UTF-8 and Unicode support for any language Tesseract supports.
    
    Args:
        image_bytes (bytes): Image file as bytes
        lang (str): Language code(s) for OCR (default: 'eng')
                    Can be single language like 'eng' or multiple like 'eng+spa+fra'
                    Use empty string or 'auto' for unknown languages
        preprocess (bool): Apply image preprocessing to improve accuracy
        psm (int): Page segmentation mode (0-13)
    
    Returns:
        dict: Dictionary containing text and detailed data (all text UTF-8 encoded)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Preprocess image if requested
        if preprocess:
            image = preprocess_image(image, enhance=True)
        
        # Build Tesseract config
        config = ''
        if psm is not None:
            config += f'--psm {psm} '
        
        # Handle unknown/unsupported languages
        if lang and lang.lower() not in ['', 'auto', 'none']:
            # Get detailed data
            data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT, config=config.strip())
            boxes = pytesseract.image_to_boxes(image, lang=lang, config=config.strip())
            text = pytesseract.image_to_string(image, lang=lang, config=config.strip())
        else:
            # Try without language specification
            if not config:
                config = '--psm 6'
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=config.strip())
            boxes = pytesseract.image_to_boxes(image, config=config.strip())
            text = pytesseract.image_to_string(image, config=config.strip())
        
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
    
    except pytesseract.TesseractError as e:
        # If language not found, try without language specification
        if 'language' in str(e).lower() or 'lang' in str(e).lower():
            try:
                image = Image.open(io.BytesIO(image_bytes))
                if preprocess:
                    image = preprocess_image(image, enhance=True)
                config = f'--psm 6' if psm is None else f'--psm {psm}'
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=config)
                boxes = pytesseract.image_to_boxes(image, config=config)
                text = pytesseract.image_to_string(image, config=config)
                if isinstance(text, bytes):
                    text = text.decode('utf-8')
                if isinstance(boxes, bytes):
                    boxes = boxes.decode('utf-8')
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
            except Exception as e2:
                raise HTTPException(
                    status_code=400,
                    detail=f"Language '{lang}' not found. Error: {str(e)}. Tried fallback mode but failed: {str(e2)}"
                )
        raise HTTPException(status_code=400, detail=f"Tesseract error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


def extract_images_from_pdf(pdf_bytes: bytes, first_page: Optional[int] = None, last_page: Optional[int] = None) -> List[dict]:
    """
    Extract embedded images from PDF pages.
    
    Args:
        pdf_bytes (bytes): PDF file as bytes
        first_page (int): First page to process (1-indexed, None = start from beginning)
        last_page (int): Last page to process (1-indexed, None = process all)
    
    Returns:
        List[dict]: List of dictionaries containing image data and page number
    """
    images_data = []
    
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        
        # Determine page range
        start_page = (first_page - 1) if first_page else 0
        end_page = last_page if last_page else total_pages
        
        # Validate page range
        if first_page and first_page < 1:
            raise HTTPException(status_code=400, detail="first_page must be >= 1")
        if last_page and last_page > total_pages:
            raise HTTPException(status_code=400, detail=f"last_page ({last_page}) exceeds total pages ({total_pages})")
        if start_page >= end_page:
            raise HTTPException(status_code=400, detail="Invalid page range")
        
        # Extract images from each page
        for page_num in range(start_page, end_page):
            page = pdf_reader.pages[page_num]
            
            if '/XObject' in page.get('/Resources', {}):
                xobjects = page['/Resources']['/XObject'].get_object()
                
                for obj_name in xobjects:
                    obj = xobjects[obj_name]
                    
                    if obj.get('/Subtype') == '/Image':
                        # Extract image data
                        try:
                            # Get image data
                            if '/Filter' in obj:
                                filter_type = obj['/Filter']
                                
                                # Handle different image formats
                                if filter_type == '/DCTDecode':  # JPEG
                                    image_data = obj.get_data()
                                    images_data.append({
                                        'page': page_num + 1,
                                        'image_data': image_data,
                                        'format': 'JPEG',
                                        'width': obj.get('/Width'),
                                        'height': obj.get('/Height')
                                    })
                                elif filter_type == '/FlateDecode' or filter_type == '/CCITTFaxDecode' or filter_type == '/JBIG2Decode':  # PNG or TIFF-like
                                    image_data = obj.get_data()
                                    images_data.append({
                                        'page': page_num + 1,
                                        'image_data': image_data,
                                        'format': 'PNG/TIFF',
                                        'width': obj.get('/Width'),
                                        'height': obj.get('/Height')
                                    })
                                else:
                                    # Try to extract anyway
                                    try:
                                        image_data = obj.get_data()
                                        images_data.append({
                                            'page': page_num + 1,
                                            'image_data': image_data,
                                            'format': 'Unknown',
                                            'width': obj.get('/Width'),
                                            'height': obj.get('/Height')
                                        })
                                    except:
                                        pass
                            else:
                                # No filter, try direct extraction
                                try:
                                    image_data = obj.get_data()
                                    images_data.append({
                                        'page': page_num + 1,
                                        'image_data': image_data,
                                        'format': 'Raw',
                                        'width': obj.get('/Width'),
                                        'height': obj.get('/Height')
                                    })
                                except:
                                    pass
                        except Exception as e:
                            # Skip images that can't be extracted
                            continue
        
        return images_data
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting images from PDF: {str(e)}")


def extract_text_from_pdf_bytes(
    pdf_bytes: bytes,
    lang: str = 'eng',
    preprocess: bool = False,
    psm: Optional[int] = None,
    first_page: Optional[int] = None,
    last_page: Optional[int] = None
) -> dict:
    """
    Extract text from PDF by extracting embedded images and running OCR on them.
    
    Args:
        pdf_bytes (bytes): PDF file as bytes
        lang (str): Language code(s) for OCR
        preprocess (bool): Apply image preprocessing
        psm (int): Page segmentation mode
        first_page (int): First page to process (1-indexed, None = start from beginning)
        last_page (int): Last page to process (1-indexed, None = process all)
    
    Returns:
        dict: Dictionary with extracted text per image/page and combined text
    """
    try:
        # Extract embedded images from PDF
        images_data = extract_images_from_pdf(pdf_bytes, first_page, last_page)
        
        if not images_data:
            return {
                'total_pages': 0,
                'images_found': 0,
                'pages_processed': 0,
                'pages': [],
                'combined_text': '',
                'text': '',
                'total_words': 0,
                'average_confidence': None,
                'pages_data': [],
                'message': 'No images found in PDF. PDF may contain only text or no embedded images.'
            }
        
        # Process each extracted image
        pages_text = []
        pages_data = []
        processed_pages = set()
        
        for img_info in images_data:
            page_num = img_info['page']
            image_data = img_info['image_data']
            
            try:
                # Try to open image from bytes
                image = Image.open(io.BytesIO(image_data))
                
                # Convert PIL image to bytes for OCR processing
                img_byte_arr = io.BytesIO()
                # Save in format that PIL can handle
                if image.format:
                    image.save(img_byte_arr, format=image.format)
                else:
                    image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                image_bytes = img_byte_arr.read()
                
                # Extract text from this image
                text = extract_text_from_image_bytes(image_bytes, lang, preprocess, psm)
                
                # Get detailed data
                try:
                    result = extract_text_with_details_bytes(image_bytes, lang, preprocess, psm)
                    word_count = result['word_count']
                    avg_confidence = result['average_confidence']
                except:
                    word_count = len([w for w in text.split() if w.strip()])
                    avg_confidence = None
                
                # Group by page number
                if page_num not in processed_pages:
                    pages_text.append({
                        'page': page_num,
                        'text': text,
                        'text_length': len(text),
                        'images_on_page': 1
                    })
                    pages_data.append({
                        'page': page_num,
                        'word_count': word_count,
                        'average_confidence': avg_confidence
                    })
                    processed_pages.add(page_num)
                else:
                    # Append to existing page text
                    for p in pages_text:
                        if p['page'] == page_num:
                            p['text'] += '\n' + text
                            p['text_length'] += len(text)
                            p['images_on_page'] += 1
                            break
                    # Update word count
                    for p in pages_data:
                        if p['page'] == page_num:
                            p['word_count'] += word_count
                            if avg_confidence and p['average_confidence']:
                                p['average_confidence'] = (p['average_confidence'] + avg_confidence) / 2
                            elif avg_confidence:
                                p['average_confidence'] = avg_confidence
                            break
                
            except Exception as e:
                # Skip images that can't be processed
                continue
        
        # Sort by page number
        pages_text.sort(key=lambda x: x['page'])
        pages_data.sort(key=lambda x: x['page'])
        
        # Combine all text
        combined_text = '\n\n'.join([f"--- Page {p['page']} ({p['images_on_page']} image(s)) ---\n{p['text']}" for p in pages_text])
        all_text = '\n'.join([p['text'] for p in pages_text])
        
        # Calculate overall statistics
        total_words = sum(p['word_count'] for p in pages_data)
        confidences = [p['average_confidence'] for p in pages_data if p['average_confidence'] is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else None
        
        # Get total pages from PDF
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        
        return {
            'total_pages': total_pages,
            'images_found': len(images_data),
            'pages_processed': len(processed_pages),
            'pages': pages_text,
            'combined_text': combined_text,
            'text': all_text,  # Simple combined text without page markers
            'total_words': total_words,
            'average_confidence': round(avg_confidence, 2) if avg_confidence else None,
            'pages_data': pages_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")


def create_csv_from_ocr_results(result: dict, filename: str = "ocr_results") -> io.BytesIO:
    """
    Create a CSV file from OCR results.
    
    Args:
        result (dict): OCR results dictionary
        filename (str): Base filename for CSV
    
    Returns:
        io.BytesIO: CSV file as bytes
    """
    csv_buffer = io.BytesIO()
    
    # Use UTF-8 encoding with BOM for Excel compatibility
    csv_buffer.write('\ufeff'.encode('utf-8'))  # BOM for Excel
    
    # Create CSV writer
    writer = csv.writer(io.TextIOWrapper(csv_buffer, encoding='utf-8', newline=''))
    
    # Write header
    writer.writerow([
        'Page',
        'Images on Page',
        'Text',
        'Word Count',
        'Average Confidence (%)',
        'Text Length'
    ])
    
    # Write data rows
    for page_info in result.get('pages', []):
        page_num = page_info.get('page', '')
        images_count = page_info.get('images_on_page', 0)
        text = page_info.get('text', '').replace('\n', ' ').replace('\r', ' ')  # Replace newlines for CSV
        text_length = page_info.get('text_length', 0)
        
        # Find corresponding page data
        page_data = next(
            (p for p in result.get('pages_data', []) if p.get('page') == page_num),
            {}
        )
        word_count = page_data.get('word_count', 0)
        avg_confidence = page_data.get('average_confidence', '')
        
        writer.writerow([
            page_num,
            images_count,
            text,
            word_count,
            avg_confidence if avg_confidence else '',
            text_length
        ])
    
    # Add summary row
    writer.writerow([])  # Empty row
    writer.writerow(['SUMMARY', '', '', '', '', ''])
    writer.writerow(['Total Pages', '', '', result.get('total_pages', 0), '', ''])
    writer.writerow(['Images Found', '', '', result.get('images_found', 0), '', ''])
    writer.writerow(['Pages Processed', '', '', result.get('pages_processed', 0), '', ''])
    writer.writerow(['Total Words', '', '', result.get('total_words', 0), '', ''])
    writer.writerow(['Average Confidence (%)', '', '', result.get('average_confidence', ''), '', ''])
    writer.writerow(['Language', '', '', result.get('language', ''), '', ''])
    writer.writerow(['Preprocessed', '', '', result.get('preprocessed', False), '', ''])
    
    csv_buffer.seek(0)
    return csv_buffer


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
            "POST /ocr/pdf": "Extract text from PDF (extracts embedded images and runs OCR). Supports CSV export with format=csv",
            "POST /ocr/pdf/detailed": "Extract text from PDF with detailed information per page. Supports CSV export with format=csv",
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
        description="Language code(s) for OCR. Single: 'eng', 'spa', 'chi_sim', 'jpn', etc. Multiple: 'eng+spa+fra'. Use empty string '' or 'auto' for unknown/unsupported languages. Supports 100+ languages with full UTF-8/Unicode support."
    ),
    preprocess: bool = Query(
        default=False,
        description="Apply image preprocessing (grayscale, contrast, sharpness) to improve OCR accuracy. Recommended for low-quality images or unknown languages."
    ),
    psm: Optional[int] = Query(
        default=None,
        description="Page Segmentation Mode (0-13). Common: 6=uniform block, 7=single line, 8=single word, 13=raw line. Leave empty for auto."
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
        text = extract_text_from_image_bytes(image_bytes, lang, preprocess=preprocess, psm=psm)
        
        # FastAPI automatically handles UTF-8 encoding in JSON responses
        response = JSONResponse(
            content={
                "success": True,
                "text": text,
                "language": lang if lang else "auto (no language specified)",
                "filename": file.filename,
                "encoding": "UTF-8",
                "preprocessed": preprocess,
                "psm_mode": psm
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
        description="Language code(s) for OCR. Single: 'eng', 'spa', 'chi_sim', 'jpn', etc. Multiple: 'eng+spa+fra'. Use empty string '' or 'auto' for unknown/unsupported languages. Supports 100+ languages with full UTF-8/Unicode support."
    ),
    preprocess: bool = Query(
        default=False,
        description="Apply image preprocessing (grayscale, contrast, sharpness) to improve OCR accuracy. Recommended for low-quality images or unknown languages."
    ),
    psm: Optional[int] = Query(
        default=None,
        description="Page Segmentation Mode (0-13). Common: 6=uniform block, 7=single line, 8=single word, 13=raw line. Leave empty for auto."
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
        result = extract_text_with_details_bytes(image_bytes, lang, preprocess=preprocess, psm=psm)
        
        # FastAPI automatically handles UTF-8 encoding in JSON responses
        response = JSONResponse(
            content={
                "success": True,
                "text": result['text'],
                "word_count": result['word_count'],
                "average_confidence": result['average_confidence'],
                "language": lang if lang else "auto (no language specified)",
                "filename": file.filename,
                "encoding": "UTF-8",
                "preprocessed": preprocess,
                "psm_mode": psm,
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


@app.post("/ocr/pdf")
async def ocr_extract_text_from_pdf(
    file: UploadFile = File(..., description="PDF file to process"),
    lang: str = Query(
        default='eng',
        description="Language code(s) for OCR. Single: 'eng', 'spa', 'chi_sim', 'jpn', etc. Multiple: 'eng+spa+fra'. Use empty string '' or 'auto' for unknown/unsupported languages."
    ),
    preprocess: bool = Query(
        default=False,
        description="Apply image preprocessing (grayscale, contrast, sharpness) to improve OCR accuracy. Recommended for low-quality PDFs or unknown languages."
    ),
    psm: Optional[int] = Query(
        default=None,
        description="Page Segmentation Mode (0-13). Common: 6=uniform block, 7=single line, 8=single word, 13=raw line. Leave empty for auto."
    ),
    first_page: Optional[int] = Query(
        default=None,
        description="First page to process (1-indexed). Leave empty to start from page 1."
    ),
    last_page: Optional[int] = Query(
        default=None,
        description="Last page to process (1-indexed). Leave empty to process all pages."
    ),
    format: str = Query(
        default='json',
        description="Output format: 'json' (default) or 'csv' for CSV download"
    )
):
    """
    Extract text from a PDF file by extracting embedded images and running OCR on them.
    Perfect for PDFs that contain scanned images or image-based content.
    
    This endpoint extracts embedded image objects from the PDF (not converting pages to images),
    then runs OCR on each extracted image to extract text.
    
    - **file**: PDF file
    - **lang**: Language code(s) (default: 'eng')
                - Single: 'eng', 'spa', 'chi_sim', 'jpn', 'kor', 'ara', etc.
                - Multiple: 'eng+spa+fra' (combine languages with '+')
                - Use empty string '' or 'auto' for unknown/unsupported languages
    - **preprocess**: Enable image preprocessing for better accuracy
    - **psm**: Page Segmentation Mode (0-13)
    - **first_page**: First page to process (1-indexed, optional)
    - **last_page**: Last page to process (1-indexed, optional)
    - **format**: Output format - 'json' (default) or 'csv' for CSV download
    
    Returns extracted text from all images found in the PDF with page-by-page breakdown.
    All text is UTF-8 encoded and supports full Unicode character sets.
    """
    try:
        # Validate file type
        if not file.content_type == 'application/pdf' and not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="File must be a PDF"
            )
        
        # Read PDF file
        pdf_bytes = await file.read()
        
        # Extract text from PDF
        result = extract_text_from_pdf_bytes(
            pdf_bytes,
            lang=lang,
            preprocess=preprocess,
            psm=psm,
            first_page=first_page,
            last_page=last_page
        )
        
        # Add metadata to result for CSV
        result['language'] = lang if lang else "auto (no language specified)"
        result['preprocessed'] = preprocess
        result['filename'] = file.filename
        
        # Return CSV if requested
        if format.lower() == 'csv':
            csv_buffer = create_csv_from_ocr_results(result, file.filename or "ocr_results")
            csv_filename = (file.filename or "ocr_results").replace('.pdf', '_ocr_results.csv')
            
            return StreamingResponse(
                io.BytesIO(csv_buffer.read()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={csv_filename}",
                    "Content-Type": "text/csv; charset=utf-8"
                }
            )
        
        # FastAPI automatically handles UTF-8 encoding in JSON responses
        response = JSONResponse(
            content={
                "success": True,
                "text": result['text'],
                "combined_text": result['combined_text'],  # With page markers
                "total_pages": result['total_pages'],
                "images_found": result.get('images_found', 0),
                "pages_processed": result['pages_processed'],
                "total_words": result['total_words'],
                "average_confidence": result['average_confidence'],
                "language": lang if lang else "auto (no language specified)",
                "filename": file.filename,
                "encoding": "UTF-8",
                "preprocessed": preprocess,
                "psm_mode": psm,
                "pages": result['pages'],  # Page-by-page text
                "pages_data": result['pages_data']  # Page-by-page statistics
            }
        )
        # Explicitly set UTF-8 charset in response header
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/ocr/pdf/detailed")
async def ocr_extract_detailed_from_pdf(
    file: UploadFile = File(..., description="PDF file to process"),
    lang: str = Query(
        default='eng',
        description="Language code(s) for OCR. Single: 'eng', 'spa', 'chi_sim', 'jpn', etc. Multiple: 'eng+spa+fra'. Use empty string '' or 'auto' for unknown/unsupported languages."
    ),
    preprocess: bool = Query(
        default=False,
        description="Apply image preprocessing (grayscale, contrast, sharpness) to improve OCR accuracy. Recommended for low-quality PDFs or unknown languages."
    ),
    psm: Optional[int] = Query(
        default=None,
        description="Page Segmentation Mode (0-13). Common: 6=uniform block, 7=single line, 8=single word, 13=raw line. Leave empty for auto."
    ),
    first_page: Optional[int] = Query(
        default=None,
        description="First page to process (1-indexed). Leave empty to start from page 1."
    ),
    last_page: Optional[int] = Query(
        default=None,
        description="Last page to process (1-indexed). Leave empty to process all pages."
    ),
    format: str = Query(
        default='json',
        description="Output format: 'json' (default) or 'csv' for CSV download"
    )
):
    """
    Extract text with detailed information from a PDF file by extracting embedded images.
    Returns page-by-page text with confidence scores, word counts, and bounding boxes.
    
    This endpoint extracts embedded image objects from the PDF (not converting pages to images),
    then runs OCR on each extracted image with detailed information.
    
    - **file**: PDF file
    - **lang**: Language code(s) (default: 'eng')
    - **preprocess**: Enable image preprocessing for better accuracy
    - **psm**: Page Segmentation Mode (0-13)
    - **first_page**: First page to process (1-indexed, optional)
    - **last_page**: Last page to process (1-indexed, optional)
    - **format**: Output format - 'json' (default) or 'csv' for CSV download
    
    Returns detailed OCR information for each image found including confidence scores and bounding boxes.
    """
    try:
        # Validate file type
        if not file.content_type == 'application/pdf' and not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="File must be a PDF"
            )
        
        # Read PDF file
        pdf_bytes = await file.read()
        
        # Extract embedded images from PDF
        images_data = extract_images_from_pdf(pdf_bytes, first_page, last_page)
        
        if not images_data:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "No images found in PDF. PDF may contain only text or no embedded images.",
                    "total_pages": 0,
                    "images_found": 0,
                    "pages_processed": 0,
                    "text": "",
                    "combined_text": "",
                    "total_words": 0,
                    "average_confidence": None,
                    "language": lang if lang else "auto (no language specified)",
                    "filename": file.filename,
                    "encoding": "UTF-8",
                    "preprocessed": preprocess,
                    "psm_mode": psm,
                    "pages": []
                }
            )
        
        # Process each extracted image with detailed information
        pages_detailed = []
        processed_pages = {}
        
        for img_info in images_data:
            page_num = img_info['page']
            image_data = img_info['image_data']
            
            try:
                # Try to open image from bytes
                image = Image.open(io.BytesIO(image_data))
                
                # Convert PIL image to bytes for OCR processing
                img_byte_arr = io.BytesIO()
                if image.format:
                    image.save(img_byte_arr, format=image.format)
                else:
                    image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                image_bytes = img_byte_arr.read()
                
                # Extract detailed information from this image
                result = extract_text_with_details_bytes(image_bytes, lang, preprocess, psm)
                
                # Group by page number
                if page_num not in processed_pages:
                    pages_detailed.append({
                        'page': page_num,
                        'text': result['text'],
                        'word_count': result['word_count'],
                        'average_confidence': result['average_confidence'],
                        'data': result['data'],
                        'boxes': result['boxes'],
                        'images_on_page': 1
                    })
                    processed_pages[page_num] = len(pages_detailed) - 1
                else:
                    # Merge with existing page data
                    idx = processed_pages[page_num]
                    pages_detailed[idx]['text'] += '\n' + result['text']
                    pages_detailed[idx]['word_count'] += result['word_count']
                    if result['average_confidence'] and pages_detailed[idx]['average_confidence']:
                        pages_detailed[idx]['average_confidence'] = (
                            pages_detailed[idx]['average_confidence'] + result['average_confidence']
                        ) / 2
                    elif result['average_confidence']:
                        pages_detailed[idx]['average_confidence'] = result['average_confidence']
                    pages_detailed[idx]['images_on_page'] += 1
                    # Merge data and boxes (simplified - you might want more sophisticated merging)
                    pages_detailed[idx]['data'] = result['data']  # Keep latest
                    pages_detailed[idx]['boxes'].extend(result['boxes'])
                
            except Exception as e:
                # Skip images that can't be processed
                continue
        
        # Sort by page number
        pages_detailed.sort(key=lambda x: x['page'])
        
        # Combine all text
        combined_text = '\n\n'.join([
            f"--- Page {p['page']} ({p['images_on_page']} image(s)) ---\n{p['text']}" 
            for p in pages_detailed
        ])
        all_text = '\n'.join([p['text'] for p in pages_detailed])
        
        # Calculate overall statistics
        total_words = sum(p['word_count'] for p in pages_detailed)
        confidences = [p['average_confidence'] for p in pages_detailed if p['average_confidence'] is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else None
        
        # Get total pages from PDF
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        
        # Prepare result dictionary for CSV or JSON
        result_dict = {
            "success": True,
            "text": all_text,
            "combined_text": combined_text,
            "total_pages": total_pages,
            "images_found": len(images_data),
            "pages_processed": len(processed_pages),
            "total_words": total_words,
            "average_confidence": round(avg_confidence, 2) if avg_confidence else None,
            "language": lang if lang else "auto (no language specified)",
            "filename": file.filename,
            "encoding": "UTF-8",
            "preprocessed": preprocess,
            "psm_mode": psm,
            "pages": [
                {
                    "page": p['page'],
                    "text": p['text'],
                    "text_length": len(p['text']),
                    "images_on_page": p['images_on_page'],
                    "word_count": p['word_count'],
                    "average_confidence": p['average_confidence']
                }
                for p in pages_detailed
            ],
            "pages_data": [
                {
                    "page": p['page'],
                    "word_count": p['word_count'],
                    "average_confidence": p['average_confidence']
                }
                for p in pages_detailed
            ]
        }
        
        # Return CSV if requested
        if format.lower() == 'csv':
            csv_buffer = create_csv_from_ocr_results(result_dict, file.filename or "ocr_results")
            csv_filename = (file.filename or "ocr_results").replace('.pdf', '_ocr_results.csv')
            
            return StreamingResponse(
                io.BytesIO(csv_buffer.read()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={csv_filename}",
                    "Content-Type": "text/csv; charset=utf-8"
                }
            )
        
        # FastAPI automatically handles UTF-8 encoding in JSON responses
        response = JSONResponse(
            content={
                "success": True,
                "text": all_text,
                "combined_text": combined_text,
                "total_pages": total_pages,
                "images_found": len(images_data),
                "pages_processed": len(processed_pages),
                "total_words": total_words,
                "average_confidence": round(avg_confidence, 2) if avg_confidence else None,
                "language": lang if lang else "auto (no language specified)",
                "filename": file.filename,
                "encoding": "UTF-8",
                "preprocessed": preprocess,
                "psm_mode": psm,
                "pages": pages_detailed  # Detailed info per page
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

