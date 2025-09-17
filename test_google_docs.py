#!/usr/bin/env python3
"""
Test script for Google Docs integration
This will test if Harry can read your actual charter
"""

import asyncio
import os
from ai_integration import AICharterAssistant

async def test_google_docs():
    """Test Google Docs integration"""
    print("🧪 Testing Google Docs Integration")
    print("=" * 40)
    print()
    
    # Check if credentials exist
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("   Run: python3 setup_google_docs.py")
        return False
    
    print("✅ credentials.json found")
    print()
    
    # Test AI integration
    ai = AICharterAssistant()
    
    print("📖 Testing charter content retrieval...")
    try:
        content = await ai.get_charter_content()
        if content and "CFB 26" in content:
            print("✅ Successfully retrieved charter content!")
            print(f"📄 Content length: {len(content)} characters")
            print()
            print("📝 First 200 characters:")
            print("-" * 40)
            print(content[:200] + "..." if len(content) > 200 else content)
            print("-" * 40)
            print()
            
            # Test AI response
            print("🤖 Testing AI response...")
            response = await ai.ask_ai("What are the recruiting rules?")
            if response:
                print("✅ AI response successful!")
                print("📝 Response:")
                print("-" * 40)
                print(response)
                print("-" * 40)
                return True
            else:
                print("❌ AI response failed")
                return False
        else:
            print("❌ Failed to retrieve charter content")
            print("   Make sure your Google Doc is shared publicly")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_google_docs())
    if success:
        print("\n🎉 Google Docs integration is working!")
        print("   Harry can now read your actual charter!")
    else:
        print("\n💡 Setup needed:")
        print("   1. Run: python3 setup_google_docs.py")
        print("   2. Follow the instructions")
        print("   3. Run this test again")
