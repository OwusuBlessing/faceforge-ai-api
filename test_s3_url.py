#!/usr/bin/env python3
"""
Test script to debug S3 URL accessibility issues
"""

import requests
import sys
from urllib.parse import urlparse

def test_url_accessibility(url: str):
    """Test if a URL is accessible and provide detailed information"""
    print(f"Testing URL: {url}")
    print("=" * 50)
    
    # Parse URL
    parsed = urlparse(url)
    print(f"Protocol: {parsed.scheme}")
    print(f"Domain: {parsed.netloc}")
    print(f"Path: {parsed.path}")
    print(f"Query: {parsed.query}")
    
    # Check if it's an S3 URL
    if 's3.' in url or 'amazonaws.com' in url:
        print("\nS3 URL detected!")
        if '?' in url and 'X-Amz-' in url:
            print("⚠️  This appears to be a pre-signed URL (may expire)")
        if not url.startswith('https://'):
            print("⚠️  S3 URL should use HTTPS")
    
    # Try to access the URL
    print(f"\nAttempting to download...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; FaceForge-AI/1.0)',
            'Accept': '*/*'
        }
        
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")
        print(f"Content-Length: {response.headers.get('Content-Length', 'Not specified')}")
        print(f"Actual Content Size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            if len(response.content) < 100:
                print("⚠️  File is very small - might be an error response")
                print(f"First 200 characters: {response.content[:200]}")
            else:
                print("✅ File appears to be accessible")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_s3_url.py <URL>")
        print("Example: python test_s3_url.py 'https://s3.us-east-2.amazonaws.com/com.mkdlabs.images/videos/audio/3b2ab4b2-fb1c-45c9-98cd-4c3613127e70-blob.mp3'")
        sys.exit(1)
    
    url = sys.argv[1]
    test_url_accessibility(url) 