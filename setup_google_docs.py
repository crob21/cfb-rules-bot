#!/usr/bin/env python3
"""
Setup script for Google Docs integration
This will help you get the Google Docs API working to read your actual charter
"""

import os
import sys

def setup_google_docs():
    """Setup Google Docs integration"""
    print("🔧 Google Docs API Setup for CFB 26 League Bot")
    print("=" * 60)
    print()
    print("This will allow Harry to read your actual Google Doc charter!")
    print()
    print("📋 Step-by-Step Instructions:")
    print()
    print("1. 🌐 Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print()
    print("2. 📁 Create a new project (or select existing):")
    print("   - Click 'Select a project' → 'New Project'")
    print("   - Name it 'CFB 26 Bot' or similar")
    print()
    print("3. 🔌 Enable Google Docs API:")
    print("   - Go to 'APIs & Services' → 'Library'")
    print("   - Search for 'Google Docs API'")
    print("   - Click 'Enable'")
    print()
    print("4. 🔑 Create credentials:")
    print("   - Go to 'APIs & Services' → 'Credentials'")
    print("   - Click 'Create Credentials' → 'OAuth 2.0 Client ID'")
    print("   - Application type: 'Desktop application'")
    print("   - Name: 'CFB 26 Bot'")
    print("   - Click 'Create'")
    print()
    print("5. 💾 Download credentials:")
    print("   - Click the download button (⬇️)")
    print("   - Save as 'credentials.json' in this folder")
    print()
    print("6. 🔗 Share your Google Doc:")
    print("   - Open your charter: https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit")
    print("   - Click 'Share' → 'Change to anyone with the link can view'")
    print("   - Or add the service account email (will be shown after first run)")
    print()
    print("7. 🚀 Test the integration:")
    print("   - Run: python3 test_google_docs.py")
    print()
    print("✨ Once set up, Harry will read your actual charter content!")
    print()
    print("⚠️  Note: This is optional! Harry works fine with just the direct link.")
    print("   The Google Docs integration just makes responses more accurate.")

def check_setup():
    """Check if Google Docs is already set up"""
    if os.path.exists('credentials.json'):
        print("✅ credentials.json found!")
        return True
    else:
        print("❌ credentials.json not found")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_setup()
    else:
        setup_google_docs()
