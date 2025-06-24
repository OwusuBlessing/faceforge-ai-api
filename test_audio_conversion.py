#!/usr/bin/env python3
"""
Test script to verify audio file download and conversion
"""

import requests
import subprocess
import tempfile
import os
from urllib.parse import urlparse

def test_audio_download_and_conversion(url: str):
    """Test downloading an audio file and converting it if needed"""
    print(f"Testing audio URL: {url}")
    print("=" * 60)
    
    # Download the file
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; FaceForge-AI/1.0)',
        'Accept': 'audio/*, */*'
    }
    
    try:
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
        response.raise_for_status()
        
        audio_data = response.content
        content_type = response.headers.get("Content-Type", "unknown")
        
        print(f"Download successful:")
        print(f"  Size: {len(audio_data)} bytes")
        print(f"  Content-Type: {content_type}")
        
        # Check file magic bytes
        if len(audio_data) >= 4:
            magic_bytes = audio_data[:4]
            print(f"  Magic bytes: {magic_bytes.hex()}")
            
            if magic_bytes.startswith(b'RIFF'):
                print("  ✅ Detected: WAV file")
            elif magic_bytes.startswith(b'ID3') or magic_bytes.startswith(b'\xff\xfb') or magic_bytes.startswith(b'\xff\xf3'):
                print("  ✅ Detected: MP3 file")
            elif magic_bytes.startswith(b'\x1a\x45\xdf\xa3'):
                print("  ⚠️  Detected: WebM file (may need conversion)")
            else:
                print(f"  ❓ Unknown format")
        
        # Test conversion if needed
        if content_type not in ["audio/mpeg", "audio/mp3"]:
            print(f"\nTesting conversion to MP3...")
            
            # Check if ffmpeg is available
            try:
                result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("  ✅ ffmpeg is available")
                    
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_file.write(audio_data)
                        input_path = temp_file.name
                    
                    output_path = input_path + ".mp3"
                    
                    try:
                        # Convert to MP3
                        cmd = [
                            'ffmpeg', '-i', input_path, 
                            '-acodec', 'libmp3lame', '-ab', '128k',
                            '-y', output_path
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0 and os.path.exists(output_path):
                            with open(output_path, 'rb') as f:
                                converted_data = f.read()
                            
                            print(f"  ✅ Conversion successful:")
                            print(f"    Original size: {len(audio_data)} bytes")
                            print(f"    Converted size: {len(converted_data)} bytes")
                            print(f"    Output file: {output_path}")
                        else:
                            print(f"  ❌ Conversion failed: {result.stderr}")
                            
                    finally:
                        # Clean up
                        try:
                            os.unlink(input_path)
                            if os.path.exists(output_path):
                                os.unlink(output_path)
                        except:
                            pass
                else:
                    print("  ❌ ffmpeg not available")
                    
            except Exception as e:
                print(f"  ❌ Error checking ffmpeg: {e}")
        else:
            print("  ✅ File is already MP3 format")
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Test both URLs
    test_urls = [
        "https://raw.githubusercontent.com/OwusuBlessing/faceforge-ai-api/master/data/sample_pics/sam_voice.mp3",
        "https://s3.us-east-2.amazonaws.com/com.mkdlabs.images/videos/audio/3b2ab4b2-fb1c-45c9-98cd-4c3613127e70-blob.mp3"
    ]
    
    for url in test_urls:
        test_audio_download_and_conversion(url)
        print() 