# TTS API - Cloudflare Pages Deployment

## 🚀 Quick Deploy to Cloudflare Pages

### Prerequisites
- Cloudflare account
- Google API key with Gemini TTS access
- Node.js and npm installed
- Git repository

### 1. Automated Setup & Deployment

The easiest way to deploy is using the provided deployment script:

```bash
# Navigate to the cloudflare directory
cd cloudflare

# Run the deployment script
chmod +x deploy.sh
./deploy.sh
```

This script will:
- ✅ Install Wrangler CLI if needed
- ✅ Authenticate with Cloudflare
- ✅ Create required KV namespaces
- ✅ Deploy your Pages project
- ✅ Provide setup instructions

### 2. Manual Setup (Alternative)

If you prefer manual setup:

#### Create KV Namespaces
```bash
# Create KV namespace for audio files
npx wrangler kv:namespace create "AUDIO_FILES"
npx wrangler kv:namespace create "AUDIO_FILES" --preview
```

#### Deploy to Cloudflare Pages

1. **Connect Repository:**
   - Go to [Cloudflare Pages Dashboard](https://dash.cloudflare.com/pages)
   - Click "Create a project"
   - Connect your Git repository
   - Select the `cloudflare` folder as build directory

2. **Configure Build Settings:**
   - Framework preset: `None`
   - Build command: `(leave empty)`
   - Build output directory: `./`

3. **Configure KV Bindings:**
   - Go to Settings > Functions
   - Add KV namespace binding:
     - Variable name: `AUDIO_FILES`
     - KV namespace: (select the one you created)

4. **Set Environment Variables (Optional):**
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```
   Note: API keys can also be provided per request if not set globally.

### 3. Test Your Deployment

Visit your Cloudflare Pages URL and test:

```bash
# Health check endpoint
curl https://your-project.pages.dev/api/test

# TTS generation endpoint
curl -X POST https://your-project.pages.dev/api/tts \
  -H "Content-Type: application/json" \
  -d '{
    "dialogue": "Speaker 1: Hello!\nSpeaker 2: Hi there!",
    "voices": {"Speaker 1": "Kore", "Speaker 2": "Puck"},
    "model": "gemini-2.5-flash-preview-tts",
    "api_key": "your-google-api-key",
    "webhook_url": "https://webhook.site/your-unique-url",
    "episode_id": "test-001"
  }'
```

## 🔧 API Endpoints

### GET `/api/test`
Health check and system status

**Response:**
```json
{
  "status": "operational",
  "message": "🎉 Cloudflare Pages Functions are working!",
  "timestamp": "2025-01-01T12:00:00.000Z",
  "version": "1.0.0",
  "environment": {
    "checks": {
      "audio_storage": true,
      "google_api_key": false,
      "host": "your-project.pages.dev"
    },
    "warnings": ["GOOGLE_API_KEY environment variable not set"]
  },
  "endpoints": {...},
  "available_voices": [...],
  "example_request": {...}
}
```

### POST `/api/tts`
Generate TTS audio from multi-speaker dialogue

**Request:**
```json
{
  "dialogue": "Speaker 1: Hello!\nSpeaker 2: Hi there!",
  "voices": {
    "Speaker 1": "Kore",
    "Speaker 2": "Puck"
  },
  "model": "gemini-2.5-flash-preview-tts",
  "api_key": "your-google-api-key",
  "webhook_url": "https://your-webhook.com/endpoint",
  "episode_id": "unique-episode-id"
}
```

**Response:**
```json
{
  "status": "completed",
  "job_id": "uuid-here",
  "audio_url": "https://your-domain.pages.dev/api/audio/uuid-here",
  "timestamp": "2025-01-01T12:00:00.000Z"
}
```

**Error Response:**
```json
{
  "error": "Missing required fields",
  "required": ["dialogue", "voices", "model", "api_key", "webhook_url", "episode_id"],
  "timestamp": "2025-01-01T12:00:00.000Z"
}
```

### GET `/api/audio/[id]`
Download generated audio file

**Parameters:**
- `id`: UUID of the generated audio file
- `download=true` (optional): Force download instead of inline playback

**Response:** WAV audio file or error JSON

**Error Response:**
```json
{
  "error": "Audio file not found",
  "message": "No audio file found with ID: uuid-here. The file may have expired or never existed."
}
```

## 🎯 Features

- ✅ **Instant Generation**: No queue system, immediate processing
- ✅ **Multi-Speaker Support**: Up to 2 speakers with different voices
- ✅ **30+ Voice Options**: All Google Gemini TTS voices available
- ✅ **Webhook Notifications**: Success/failure callbacks with timestamps
- ✅ **CORS Enabled**: Works from any frontend
- ✅ **Global Edge**: Cloudflare's worldwide network
- ✅ **No Timeouts**: Handles long audio generation
- ✅ **Automatic Cleanup**: Audio files expire after 24 hours
- ✅ **Input Validation**: Comprehensive request validation
- ✅ **Error Handling**: Detailed error messages and logging
- ✅ **UUID Validation**: Secure audio file access

## 🎭 Available Voices

| Voice | Style | Voice | Style |
|-------|-------|-------|-------|
| Zephyr | Bright | Puck | Upbeat |
| Kore | Firm | Fenrir | Excitable |
| Orus | Firm | Aoede | Breezy |
| Autonoe | Bright | Enceladus | Breathy |
| Umbriel | Easy-going | Algieba | Smooth |
| Erinome | Clear | Algenib | Gravelly |
| Laomedeia | Upbeat | Achernar | Soft |
| Schedar | Even | Gacrux | Mature |
| Achird | Friendly | Zubenelgenubi | Casual |
| Sadachbia | Lively | Sadaltager | Knowledgeable |

## 🔐 Security & Validation

- ✅ **API Key Security**: Keys processed server-side only
- ✅ **Input Validation**: 
  - Dialogue length limit (5000 characters)
  - UUID format validation for audio IDs
  - Required field validation
  - Voice configuration validation
- ✅ **Auto-Expiration**: Audio files expire after 24 hours
- ✅ **Error Boundaries**: Graceful error handling with detailed messages
- ✅ **CORS Protection**: Configurable cross-origin access
- ✅ **Rate Limiting**: Consider implementing for production use

## 📝 Usage Examples

### Podcast Generation
```javascript
const response = await fetch('/api/tts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    dialogue: `Host: Welcome to our show!
Guest: Thanks for having me!`,
    voices: {
      "Host": "Kore",
      "Guest": "Puck"
    },
    model: "gemini-2.5-flash-preview-tts",
    api_key: "your-key",
    webhook_url: "https://webhook.site/your-id",
    episode_id: "episode-001"
  })
});
```

### Audiobook Narration
```javascript
const response = await fetch('/api/tts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    dialogue: `Narrator: Chapter One. The story begins...
Character: I never expected this to happen.`,
    voices: {
      "Narrator": "Gacrux",
      "Character": "Enceladus"
    },
    model: "gemini-2.5-flash-preview-tts",
    api_key: "your-key",
    webhook_url: "https://webhook.site/your-id",
    episode_id: "chapter-001"
  })
});
```

## 🚨 Troubleshooting

### Common Issues

1. **"Storage not configured" error**
   - Ensure AUDIO_FILES KV namespace is created and bound
   - Check Cloudflare Pages Settings → Functions → KV namespace bindings

2. **"Audio file not found" error**
   - Audio files expire after 24 hours
   - Verify the UUID format is correct
   - Check if the file was successfully generated

3. **"Google API error" responses**
   - Verify your Google API key has TTS access
   - Check API quota and billing
   - Ensure the model name is correct

4. **Audio not playing in browser**
   - Check browser audio permissions
   - Try adding `download=true` parameter to force download
   - Verify the audio file isn't corrupted

5. **CORS errors in frontend**
   - All endpoints include CORS headers
   - Check if requests include proper Content-Type headers
   - Verify the request format matches the documentation

### Validation Errors

- **Dialogue too long**: Maximum 5000 characters
- **Invalid audio ID**: Must be a valid UUID format
- **Missing required fields**: Check the required fields list in error response
- **Invalid voice configuration**: Must be an object with speaker names as keys

## 💡 Pro Tips

1. **Optimize Performance**: Keep dialogue under 1000 characters for faster generation
2. **Voice Selection**: Match voice personality to speaker role for better results
3. **Error Handling**: Always handle both success and error responses in your application
4. **Webhook Testing**: Use [webhook.site](https://webhook.site) for development testing
5. **Monitor Usage**: Track Google API quota consumption in Google Cloud Console
6. **Caching**: Audio files are cached with 1-hour cache headers for better performance
7. **Security**: Consider implementing authentication for production deployments

## 🔄 Recent Updates

- ✅ Fixed variable scoping issues in error handling
- ✅ Added comprehensive input validation
- ✅ Improved error messages with timestamps
- ✅ Added automatic audio file expiration (24 hours)
- ✅ Enhanced CORS support across all endpoints
- ✅ Added UUID validation for audio file access
- ✅ Updated wrangler.toml with proper compatibility settings
- ✅ Improved deployment script with automated KV setup 