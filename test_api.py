"""
Example script to test the OCR API endpoints
Requires: pip install requests
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_languages():
    """Test languages endpoint."""
    print("Testing languages endpoint...")
    response = requests.get(f"{API_BASE_URL}/languages")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_ocr(image_path, lang='eng'):
    """Test basic OCR endpoint."""
    print(f"Testing OCR endpoint with {image_path}...")
    with open(image_path, 'rb') as f:
        files = {'file': f}
        params = {'lang': lang}
        response = requests.post(
            f"{API_BASE_URL}/ocr",
            files=files,
            params=params
        )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success', False)}")
    print(f"Text: {result.get('text', '')[:200]}...")  # First 200 chars
    print()


def test_ocr_detailed(image_path, lang='eng'):
    """Test detailed OCR endpoint."""
    print(f"Testing detailed OCR endpoint with {image_path}...")
    with open(image_path, 'rb') as f:
        files = {'file': f}
        params = {'lang': lang}
        response = requests.post(
            f"{API_BASE_URL}/ocr/detailed",
            files=files,
            params=params
        )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success', False)}")
    print(f"Word Count: {result.get('word_count', 0)}")
    print(f"Average Confidence: {result.get('average_confidence', 0)}%")
    print(f"Text: {result.get('text', '')[:200]}...")  # First 200 chars
    print()


if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("OCR API Test Script")
    print("=" * 50)
    print()
    
    # Test health check
    try:
        test_health_check()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running:")
        print("  python api.py")
        sys.exit(1)
    
    # Test languages
    test_languages()
    
    # Test OCR if image path provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        lang = sys.argv[2] if len(sys.argv) > 2 else 'eng'
        
        test_ocr(image_path, lang)
        test_ocr_detailed(image_path, lang)
    else:
        print("To test OCR endpoints, provide an image path:")
        print("  python test_api.py image.png [lang]")
        print("  Example: python test_api.py image.png eng")

