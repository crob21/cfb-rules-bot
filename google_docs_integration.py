#!/usr/bin/env python3
"""
Google Docs integration for CFB 26 League Bot
This module handles fetching content from the official league charter Google Doc
"""

import os
import json
import re
from typing import Dict, List, Optional

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    print("⚠️  Google APIs not available. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

class GoogleDocsIntegration:
    """Handle Google Docs API integration for league charter"""
    
    def __init__(self):
        self.service = None
        self.document_id = "1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8"
        self.credentials_file = "credentials.json"
        self.token_file = "token.pickle"
        
    def authenticate(self):
        """Authenticate with Google Docs API"""
        if not GOOGLE_APIS_AVAILABLE:
            return False
            
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print("❌ credentials.json not found. Please download from Google Cloud Console")
                    return False
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, 
                    ['https://www.googleapis.com/auth/documents.readonly']
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('docs', 'v1', credentials=creds)
            return True
        except Exception as e:
            print(f"❌ Error building Google Docs service: {e}")
            return False
    
    def get_document_content(self) -> Optional[str]:
        """Fetch the full content of the league charter document"""
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            document = self.service.documents().get(documentId=self.document_id).execute()
            content = document.get('body', {}).get('content', [])
            
            # Extract text from document content
            text_content = []
            for element in content:
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    for text_run in paragraph.get('elements', []):
                        if 'textRun' in text_run:
                            text_content.append(text_run['textRun']['content'])
            
            return ''.join(text_content)
        except Exception as e:
            print(f"❌ Error fetching document: {e}")
            return None
    
    def search_document(self, search_term: str) -> List[str]:
        """Search for specific terms in the document"""
        content = self.get_document_content()
        if not content:
            return []
        
        # Simple text search (case insensitive)
        lines = content.split('\n')
        matching_lines = []
        
        for line in lines:
            if search_term.lower() in line.lower() and line.strip():
                matching_lines.append(line.strip())
        
        return matching_lines[:5]  # Return first 5 matches
    
    def extract_rules_sections(self) -> Dict[str, str]:
        """Extract different rule sections from the document"""
        content = self.get_document_content()
        if not content:
            return {}
        
        # Define section patterns (you can customize these based on your document structure)
        sections = {
            'recruiting': [],
            'transfers': [],
            'gameplay': [],
            'scheduling': [],
            'conduct': []
        }
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect section headers
            if 'recruiting' in line_lower:
                current_section = 'recruiting'
            elif 'transfer' in line_lower:
                current_section = 'transfers'
            elif 'gameplay' in line_lower or 'game play' in line_lower:
                current_section = 'gameplay'
            elif 'schedule' in line_lower:
                current_section = 'scheduling'
            elif 'conduct' in line_lower or 'behavior' in line_lower:
                current_section = 'conduct'
            
            # Add content to current section
            if current_section and line.strip():
                sections[current_section].append(line.strip())
        
        # Convert lists to strings
        return {k: '\n'.join(v[:10]) for k, v in sections.items() if v}  # Limit to 10 lines per section

def setup_google_docs():
    """Setup instructions for Google Docs integration"""
    print("🔧 Google Docs API Setup Instructions:")
    print("=" * 50)
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable Google Docs API")
    print("4. Create credentials (OAuth 2.0 Client ID)")
    print("5. Download credentials.json to this directory")
    print("6. Install required packages:")
    print("   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    print("7. Make sure your Google Doc is shared with the service account email")
    print("\n📝 Note: This is optional. The bot works fine with just the direct link!")

if __name__ == "__main__":
    setup_google_docs()
