# Google Docs Integration Setup

This guide will help you set up the bot to directly read from your Google Doc charter.

## Option 1: Simple Link Integration (Recommended)

The bot already includes direct links to your charter in every response. This is the simplest approach and works immediately.

**Commands available:**
- `/charter` - Get direct link to the charter
- `/search <term>` - Will show a link to search manually in the doc

## Option 2: Full Google Docs API Integration

For advanced users who want the bot to actually read and search the document content.

### Prerequisites

1. **Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Docs API

2. **OAuth Credentials**
   - Go to "Credentials" in the Google Cloud Console
   - Create "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the credentials file as `credentials.json`

3. **Document Permissions**
   - Share your Google Doc with the service account email
   - Or make the document publicly readable

### Installation

1. **Install Google APIs**
   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

2. **Setup Credentials**
   ```bash
   # Place your credentials.json file in the bot directory
   cp /path/to/your/credentials.json ./credentials.json
   ```

3. **First Run Authentication**
   ```bash
   python bot.py
   # The bot will open a browser window for OAuth authentication
   # This only needs to be done once
   ```

### Features with Google Docs Integration

- **`/search <term>`** - Actually searches the document content
- **Automatic rule extraction** - Can parse sections from your document
- **Real-time updates** - Always gets the latest version of your charter

### Troubleshooting

**"credentials.json not found"**
- Make sure you downloaded the OAuth credentials from Google Cloud Console
- Place the file in the same directory as `bot.py`

**"Document not accessible"**
- Check that your Google Doc is shared with the service account
- Or make the document publicly readable

**"Authentication failed"**
- Delete `token.pickle` and run the bot again
- Make sure you have the correct OAuth credentials

## Recommendation

For most users, **Option 1 (Simple Link Integration)** is perfect. It's:
- ✅ Easy to set up
- ✅ Always works
- ✅ No authentication needed
- ✅ Always shows the latest version

Option 2 is only needed if you want the bot to actually parse and search the document content automatically.

## Your Charter Link

Your league charter is already integrated: [CFB 26 League Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)
