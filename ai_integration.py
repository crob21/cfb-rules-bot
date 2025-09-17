#!/usr/bin/env python3
"""
AI Integration for CFB 26 League Bot
This module handles AI-powered responses about the league charter
"""

import os
import json
import aiohttp
import asyncio
from typing import Dict, List, Optional

class AICharterAssistant:
    """AI-powered assistant for league charter questions"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.charter_url = "https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit"
        self.charter_content = None
        
    async def get_charter_content(self) -> Optional[str]:
        """Get charter content for AI context"""
        # For now, we'll use a placeholder. In a real implementation,
        # you'd fetch the actual content from Google Docs or provide it manually
        return """
        CFB 26 League Charter - Key Rules and Policies:
        
        RECRUITING:
        - Each team can recruit up to 25 players per season
        - Official visits limited to 5 per player
        - Dead periods: No recruiting during finals week
        
        TRANSFERS:
        - Transfer portal opens after bowl season
        - Players must sit out one year unless graduate transfer
        - Maximum 3 transfers per team per season
        
        GAMEPLAY:
        - All-American difficulty required
        - Custom sliders: CPU QB accuracy 25, User pass coverage 75
        - No simming games without commissioner approval
        
        SCHEDULING:
        - Advance schedule every 48 hours
        - Conference games must be played first
        - Bye weeks allowed only during mid-season
        
        CONDUCT:
        - Respectful communication in Discord required
        - No trash talking during games
        - Report disputes to commissioners within 24 hours
        """
    
    async def ask_openai(self, question: str, context: str) -> Optional[str]:
        """Ask OpenAI about the charter"""
        if not self.openai_api_key:
            return None
            
        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        prompt = f"""
        You are Harry, a friendly and knowledgeable assistant for the CFB 26 online dynasty league. 
        Answer questions based on the league charter provided below in a conversational, helpful way.
        
        League Charter Context:
        {context}
        
        Question: {question}
        
        Please provide a helpful, accurate answer based on the charter. Be friendly and conversational, 
        as if you're a knowledgeable league member helping out a friend. If the information isn't in the 
        charter, say so and suggest checking the full charter. Keep responses informative but not too formal.
        """
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are Harry, a friendly and knowledgeable assistant for the CFB 26 league charter. Be conversational and helpful.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 500,
            'temperature': 0.7
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        print(f"OpenAI API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return None
    
    async def ask_anthropic(self, question: str, context: str) -> Optional[str]:
        """Ask Anthropic Claude about the charter"""
        if not self.anthropic_api_key:
            return None
            
        headers = {
            'x-api-key': self.anthropic_api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        prompt = f"""
        You are an AI assistant for the CFB 26 online dynasty league. 
        Answer questions based on the league charter provided below.
        
        League Charter Context:
        {context}
        
        Question: {question}
        
        Please provide a helpful, accurate answer based on the charter. 
        If the information isn't in the charter, say so and suggest checking the full charter.
        Keep responses concise but informative.
        """
        
        data = {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 500,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['content'][0]['text'].strip()
                    else:
                        print(f"Anthropic API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error calling Anthropic: {e}")
            return None
    
    async def ask_ai(self, question: str) -> Optional[str]:
        """Ask AI about the charter (tries OpenAI first, then Anthropic)"""
        context = await self.get_charter_content()
        if not context:
            return None
        
        # Try OpenAI first
        response = await self.ask_openai(question, context)
        if response:
            return response
        
        # Fallback to Anthropic
        response = await self.ask_anthropic(question, context)
        return response

def setup_ai_integration():
    """Setup instructions for AI integration"""
    print("🤖 AI Integration Setup Instructions:")
    print("=" * 50)
    print("Choose your AI provider:")
    print()
    print("1. OpenAI (GPT-3.5/GPT-4)")
    print("   - Go to: https://platform.openai.com/api-keys")
    print("   - Create an API key")
    print("   - Add to .env: OPENAI_API_KEY=your_key_here")
    print()
    print("2. Anthropic (Claude)")
    print("   - Go to: https://console.anthropic.com/")
    print("   - Create an API key")
    print("   - Add to .env: ANTHROPIC_API_KEY=your_key_here")
    print()
    print("3. Both (recommended for reliability)")
    print("   - Set up both APIs")
    print("   - Bot will try OpenAI first, then Anthropic as fallback")
    print()
    print("📝 Note: AI integration is optional. The bot works great without it!")

if __name__ == "__main__":
    setup_ai_integration()
