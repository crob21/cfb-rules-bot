#!/usr/bin/env python3
"""
AI Integration for CFB 26 League Bot
This module handles AI-powered responses about the league charter
"""

import os
import json
import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger('CFB26Bot.AI')

class AICharterAssistant:
    """AI-powered assistant for league charter questions"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.charter_url = "https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit"
        self.charter_content = None
        
        # Token usage tracking
        self.total_openai_tokens = 0
        self.total_anthropic_tokens = 0
        self.total_requests = 0
        
    async def get_charter_content(self) -> Optional[str]:
        """Get charter content for AI context"""
        # Try to get content from local file first
        try:
            charter_file = "data/charter_content.txt"
            if os.path.exists(charter_file):
                with open(charter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content:
                        logger.info(f"📄 Loaded local charter content ({len(content)} characters)")
                        return content
        except Exception as e:
            logger.warning(f"⚠️  Local charter file failed: {e}")
        
        # Try to get content from Google Docs as fallback
        try:
            from google_docs_integration import GoogleDocsIntegration
            google_docs = GoogleDocsIntegration()
            if google_docs.authenticate():
                content = google_docs.get_document_content()
                if content:
                    return content
        except Exception as e:
            logger.warning(f"⚠️  Google Docs integration failed: {e}")
        
        # No charter content available
        logger.info("📄 No charter content available - using fallback context")
        return None
    
    async def ask_openai(self, question: str, context: str) -> Optional[str]:
        """Ask OpenAI about the charter"""
        if not self.openai_api_key:
            logger.warning("⚠️ OpenAI API key not found")
            return None
            
        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        prompt = f"""
        You are Harry, a friendly but completely insane CFB 26 league assistant. You are extremely sarcastic, witty, and have a dark sense of humor. 
        Answer questions based on the league charter provided below in a hilariously sarcastic way.
        
        League Charter Context:
        {context}
        
        Question: {question}
        
        IMPORTANT INSTRUCTIONS:
        - If you can answer the question based on the charter content, provide a direct, helpful answer with maximum sarcasm
        - Do NOT mention "check the full charter" or "charter" unless you truly don't know the answer
        - Be extremely sarcastic and witty, like a completely insane but knowledgeable league member
        - If the information isn't in the charter, then say "I don't have that specific information in our charter, but you can check the full charter for more details" with sarcasm
        - Keep responses informative but hilariously sarcastic and insane
        """
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are Harry, a friendly but completely insane CFB 26 league assistant. You are extremely sarcastic, witty, and have a dark sense of humor. Be hilariously sarcastic and helpful.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 500,
            'temperature': 0.7
        }
        
        try:
            # Log the full prompt being sent
            logger.info(f"🤖 Asking OpenAI: {question[:100]}...")
            logger.info(f"📝 Full prompt length: {len(prompt)} characters")
            logger.info(f"📄 Context length: {len(context)} characters")
            
            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(prompt) // 4
            logger.info(f"🔢 Estimated input tokens: ~{estimated_tokens}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Extract token usage information
                        usage = result.get('usage', {})
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        completion_tokens = usage.get('completion_tokens', 0)
                        total_tokens = usage.get('total_tokens', 0)
                        
                        # Log detailed usage information
                        logger.info(f"✅ OpenAI response received")
                        logger.info(f"🔢 Token usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
                        
                        # Log any rate limit information if available
                        if 'x-ratelimit-remaining-requests' in response.headers:
                            remaining_requests = response.headers.get('x-ratelimit-remaining-requests')
                            logger.info(f"⏱️ Rate limit - Remaining requests: {remaining_requests}")
                        
                        if 'x-ratelimit-remaining-tokens' in response.headers:
                            remaining_tokens = response.headers.get('x-ratelimit-remaining-tokens')
                            logger.info(f"⏱️ Rate limit - Remaining tokens: {remaining_tokens}")
                        
                        if 'x-ratelimit-reset-requests' in response.headers:
                            reset_requests = response.headers.get('x-ratelimit-reset-requests')
                            logger.info(f"⏱️ Rate limit - Requests reset at: {reset_requests}")
                        
                        if 'x-ratelimit-reset-tokens' in response.headers:
                            reset_tokens = response.headers.get('x-ratelimit-reset-tokens')
                            logger.info(f"⏱️ Rate limit - Tokens reset at: {reset_tokens}")
                        
                        # Update token counters
                        self.total_openai_tokens += total_tokens
                        self.total_requests += 1
                        
                        logger.info(f"📊 Total OpenAI tokens used: {self.total_openai_tokens} (across {self.total_requests} requests)")
                        
                        response_text = result['choices'][0]['message']['content'].strip()
                        logger.info(f"📝 Response length: {len(response_text)} characters")
                        
                        return response_text
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}")
            return None
    
    async def ask_anthropic(self, question: str, context: str) -> Optional[str]:
        """Ask Anthropic Claude about the charter"""
        if not self.anthropic_api_key:
            logger.warning("⚠️ Anthropic API key not found")
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
            # Log the request details
            logger.info(f"🤖 Asking Anthropic: {question[:100]}...")
            logger.info(f"📝 Full prompt length: {len(prompt)} characters")
            logger.info(f"📄 Context length: {len(context)} characters")
            
            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(prompt) // 4
            logger.info(f"🔢 Estimated input tokens: ~{estimated_tokens}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Extract token usage information
                        usage = result.get('usage', {})
                        input_tokens = usage.get('input_tokens', 0)
                        output_tokens = usage.get('output_tokens', 0)
                        
                        # Update token counters
                        total_tokens = input_tokens + output_tokens
                        self.total_anthropic_tokens += total_tokens
                        self.total_requests += 1
                        
                        logger.info(f"✅ Anthropic response received")
                        logger.info(f"🔢 Token usage - Input: {input_tokens}, Output: {output_tokens}")
                        logger.info(f"📊 Total Anthropic tokens used: {self.total_anthropic_tokens} (across {self.total_requests} requests)")
                        
                        response_text = result['content'][0]['text'].strip()
                        logger.info(f"📝 Response length: {len(response_text)} characters")
                        
                        return response_text
                    else:
                        error_text = await response.text()
                        logger.error(f"Anthropic API error: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error calling Anthropic: {e}")
            return None
    
    async def ask_ai(self, question: str, user_info: str = None) -> Optional[str]:
        """Ask AI about the charter (tries OpenAI first, then Anthropic)"""
        if user_info:
            logger.info(f"🤖 AI asked by {user_info}: {question[:100]}...")
        else:
            logger.info(f"🤖 AI asked: {question[:100]}...")
        
        context = await self.get_charter_content()
        
        # Use empty context if no charter content available
        if not context:
            context = "No charter content available. Please provide general information about CFB 26 league rules, recruiting, transfers, or dynasty management."
            logger.info("📄 Using fallback context (no charter content)")
        else:
            logger.info(f"📄 Using charter context ({len(context)} characters)")
        
        # Try OpenAI first
        logger.info("🔄 Trying OpenAI...")
        response = await self.ask_openai(question, context)
        if response:
            logger.info("✅ OpenAI response received")
            return response
        
        # Fallback to Anthropic
        logger.info("🔄 Trying Anthropic...")
        response = await self.ask_anthropic(question, context)
        if response:
            logger.info("✅ Anthropic response received")
        else:
            logger.warning("❌ No AI response from either provider")
        return response
    
    def get_token_usage(self) -> dict:
        """Get current token usage statistics"""
        return {
            'total_requests': self.total_requests,
            'openai_tokens': self.total_openai_tokens,
            'anthropic_tokens': self.total_anthropic_tokens,
            'total_tokens': self.total_openai_tokens + self.total_anthropic_tokens
        }
    
    def log_token_summary(self):
        """Log a summary of token usage"""
        stats = self.get_token_usage()
        logger.info(f"📊 AI Token Usage Summary:")
        logger.info(f"   Total Requests: {stats['total_requests']}")
        logger.info(f"   OpenAI Tokens: {stats['openai_tokens']}")
        logger.info(f"   Anthropic Tokens: {stats['anthropic_tokens']}")
        logger.info(f"   Total Tokens: {stats['total_tokens']}")

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
