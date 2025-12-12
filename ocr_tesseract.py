"""
OCR (Optical Character Recognition) using Tesseract
Extracts text from images using pytesseract library
"""

import pytesseract
from PIL import Image
import argparse
import sys
import os


def extract_text_from_image(image_path, lang='eng'):
    """
    Extract text from an image file using Tesseract OCR.
    
    Args:
        image_path (str): Path to the image file
        lang (str): Language code for OCR (default: 'eng')
    
    Returns:
        str: Extracted text from the image
    """
    try:
        # Check if image file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Open image using PIL
        image = Image.open(image_path)
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(image, lang=lang)
        
        return text
    
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")


def extract_text_with_details(image_path, lang='eng'):
    """
    Extract text with detailed information (bounding boxes, confidence scores).
    
    Args:
        image_path (str): Path to the image file
        lang (str): Language code for OCR (default: 'eng')
    
    Returns:
        dict: Dictionary containing text and detailed data
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        image = Image.open(image_path)
        
        # Get detailed data
        data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        
        # Get text with bounding boxes
        boxes = pytesseract.image_to_boxes(image, lang=lang)
        
        # Get text
        text = pytesseract.image_to_string(image, lang=lang)
        
        return {
            'text': text,
            'data': data,
            'boxes': boxes
        }
    
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")


def save_text_to_file(text, output_path):
    """
    Save extracted text to a file.
    
    Args:
        text (str): Text to save
        output_path (str): Path to output file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Text saved to: {output_path}")
    except Exception as e:
        raise Exception(f"Error saving file: {str(e)}")


def main():
    """Main function to run OCR from command line."""
    parser = argparse.ArgumentParser(
        description='OCR (Optical Character Recognition) using Tesseract',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ocr_tesseract.py image.png
  python ocr_tesseract.py image.png -o output.txt
  python ocr_tesseract.py image.png -l spa
  python ocr_tesseract.py image.png --detailed
        """
    )
    
    parser.add_argument('image_path', help='Path to the image file')
    parser.add_argument('-o', '--output', help='Output file path to save extracted text')
    parser.add_argument('-l', '--lang', default='eng', help='Language code (default: eng)')
    parser.add_argument('-d', '--detailed', action='store_true', 
                       help='Show detailed OCR information (bounding boxes, confidence)')
    
    args = parser.parse_args()
    
    try:
        print(f"Processing image: {args.image_path}")
        print(f"Language: {args.lang}")
        print("-" * 50)
        
        if args.detailed:
            # Get detailed information
            result = extract_text_with_details(args.image_path, args.lang)
            print("\nExtracted Text:")
            print("=" * 50)
            print(result['text'])
            print("=" * 50)
            
            # Show some statistics
            words = [w for w in result['data']['text'] if w.strip()]
            confidences = [int(c) for c in result['data']['conf'] if c != '-1']
            
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                print(f"\nStatistics:")
                print(f"  Words detected: {len(words)}")
                print(f"  Average confidence: {avg_confidence:.2f}%")
        else:
            # Simple text extraction
            text = extract_text_from_image(args.image_path, args.lang)
            print("\nExtracted Text:")
            print("=" * 50)
            print(text)
            print("=" * 50)
            
            # Save to file if output path is provided
            if args.output:
                save_text_to_file(text, args.output)
        
        print("\nOCR completed successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


