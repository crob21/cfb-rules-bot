#!/usr/bin/env python3
"""
Setup script for CFB Rules Bot
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🏈 Setting up CFB Rules Bot...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        try:
            with open('env.example', 'r') as f:
                content = f.read()
            with open('.env', 'w') as f:
                f.write(content)
            print("✅ .env file created")
            print("⚠️  Please edit .env file with your Discord bot token")
        except FileNotFoundError:
            print("❌ env.example file not found")
            return False
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your Discord bot token")
    print("2. Run: python bot.py")
    print("3. Use /help_cfb in Discord to see available commands")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
