"""
Test script for OCR with unknown/unsupported languages
This demonstrates how to use the new features for better results
"""

import requests
import json

API_BASE_URL = "http://localhost:8080"

def test_unknown_language(image_path):
    """
    Test OCR with multiple strategies for unknown languages.
    """
    print("=" * 70)
    print("Testing OCR for Unknown/Unsupported Language")
    print("=" * 70)
    print()
    
    strategies = [
        {
            "name": "Strategy 1: Auto mode + Preprocessing + PSM 6 (Uniform block)",
            "params": {'lang': '', 'preprocess': 'true', 'psm': 6}
        },
        {
            "name": "Strategy 2: Auto mode + Preprocessing + PSM 7 (Single line)",
            "params": {'lang': '', 'preprocess': 'true', 'psm': 7}
        },
        {
            "name": "Strategy 3: Auto mode + Preprocessing + PSM 8 (Single word)",
            "params": {'lang': '', 'preprocess': 'true', 'psm': 8}
        },
        {
            "name": "Strategy 4: Auto mode + Preprocessing + PSM 13 (Raw line)",
            "params": {'lang': '', 'preprocess': 'true', 'psm': 13}
        },
        {
            "name": "Strategy 5: Auto mode + Preprocessing (no PSM)",
            "params": {'lang': '', 'preprocess': 'true'}
        },
    ]
    
    best_result = None
    best_confidence = 0
    best_strategy = None
    
    for strategy in strategies:
        print(f"\n{strategy['name']}")
        print("-" * 70)
        
        try:
            with open(image_path, 'rb') as f:
                response = requests.post(
                    f"{API_BASE_URL}/ocr/detailed",
                    files={'file': f},
                    params=strategy['params']
                )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '').strip()
                confidence = result.get('average_confidence', 0)
                word_count = result.get('word_count', 0)
                
                print(f"Status: Success")
                print(f"Word Count: {word_count}")
                print(f"Average Confidence: {confidence}%")
                print(f"Text Length: {len(text)} characters")
                
                if text:
                    preview = text[:150] if len(text) > 150 else text
                    print(f"Text Preview: {preview}")
                    if len(text) > 150:
                        print(f"... (truncated, full text is {len(text)} chars)")
                else:
                    print("Text: [EMPTY - No text detected]")
                
                # Track best result
                if text and confidence > best_confidence:
                    best_confidence = confidence
                    best_result = result
                    best_strategy = strategy['name']
            else:
                print(f"Status: Error {response.status_code}")
                print(f"Response: {response.text}")
        
        except FileNotFoundError:
            print(f"Error: Image file not found: {image_path}")
            return
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if best_result:
        print(f"\n✅ Best Result: {best_strategy}")
        print(f"   Confidence: {best_result['average_confidence']}%")
        print(f"   Word Count: {best_result['word_count']}")
        print(f"\n   Extracted Text:")
        print("   " + "-" * 66)
        text = best_result['text']
        # Print text with proper line breaks
        for line in text.split('\n'):
            if line.strip():
                print(f"   {line}")
        print("   " + "-" * 66)
    else:
        print("\n❌ No text was extracted from any strategy.")
        print("\nSuggestions:")
        print("  1. Check image quality - ensure text is clear and readable")
        print("  2. Try improving image resolution (at least 300 DPI)")
        print("  3. Ensure good contrast between text and background")
        print("  4. Check if image contains actual printed text (not handwriting)")
        print("  5. Consider training a custom Tesseract model for your language")
        print("     See UNKNOWN_LANGUAGES.md for details")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_unknown_language.py <image_path>")
        print("\nExample:")
        print("  python test_unknown_language.py image.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_unknown_language(image_path)

