#!/usr/bin/env python3
"""
Email Setup Script for Smart Inbox Assistant
This script helps you configure your email credentials securely.
"""

import sys
import os

def main():
    print("🔐 Smart Inbox Assistant - Email Setup")
    print("=" * 50)
    print()
    print("This script will help you set up your email credentials securely.")
    print("Your credentials will be encrypted and stored locally.")
    print()
    
    try:
        from credentials_manager import setup_email_credentials
        
        print("📧 Setting up email credentials...")
        credentials = setup_email_credentials()
        
        if credentials:
            print("\n✅ Email setup completed successfully!")
            print(f"📧 Email: {credentials['email_address']}")
            print(f"🔧 Provider: {credentials['provider']}")
            print()
            print("🚀 You can now run the Smart Inbox Assistant:")
            print("   python main.py")
            print("   streamlit run dashboard.py")
            print()
            print("💡 Your credentials are stored securely and encrypted.")
            print("   You won't need to enter them again unless you change them.")
        else:
            print("\n❌ Email setup failed or was cancelled.")
            print("You can still use the app with mock emails.")
            
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Please make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
