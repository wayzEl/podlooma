# TTS API - Cloudflare Pages Deployment

## 🚀 Quick Deploy to Cloudflare Pages

### Prerequisites
- Cloudflare account
- Google API key with Gemini TTS access
- Git repository

### 1. Setup Cloudflare KV Storage

```bash
# Create KV namespace for audio files
npx wrangler kv:namespace create "AUDIO_FILES"
npx wrangler kv:namespace create "AUDIO_FILES" --preview
```

### 2. Deploy to Cloudflare Pages

1. **Connect Repository:**
   - Go to [Cloudflare Pages Dashboard](https://dash.cloudflare.com/pages)
   - Click "Create a project"
   - Connect your Git repository
   - Select the `cloudflare` folder as build directory

2. **Configure Build Settings:**
   - Framework preset: `None`
   - Build command: `(leave empty)`
   - Build output directory: `./`

3. **Set Environment Variables:**
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

4. **Configure KV Bindings:**
   - Go to Settings > Functions
   - Add KV namespace binding:
     - Variable name: `AUDIO_FILES`
     - KV namespace: (select the one you created)

### 3. Test Your Deployment

Visit your Cloudflare Pages URL and test the TTS generation!

## 🔧 API Endpoints

### POST `/api/tts`
Generate TTS audio from text

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
  "audio_url": "https://your-domain.pages.dev/api/audio/uuid-here"
}
```

### GET `/api/audio/[id]`
Download generated audio file

Returns WAV audio file for the given job ID.

## 🎯 Features

- ✅ **Instant Generation**: No queue system, immediate processing
- ✅ **Multi-Speaker Support**: Up to 2 speakers with different voices
- ✅ **30+ Voice Options**: All Google Gemini TTS voices available
- ✅ **Webhook Notifications**: Success/failure callbacks
- ✅ **CORS Enabled**: Works from any frontend
- ✅ **Global Edge**: Cloudflare's worldwide network
- ✅ **No Timeouts**: Handles long audio generation

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

## 🔐 Security Notes

- API keys are processed server-side only
- Audio files stored temporarily in KV storage
- Consider implementing rate limiting for production
- Use webhook URLs with authentication in production

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
    // ... rest of config
  })
});
```

## 🚨 Troubleshooting

- **Audio not playing**: Check browser audio permissions
- **API errors**: Verify Google API key has TTS access
- **Large files**: Cloudflare Pages has 25MB response limit
- **Rate limits**: Google TTS has usage quotas

## 💡 Pro Tips

1. **Optimize dialogue length**: Keep under 1000 characters for faster generation
2. **Choose voices wisely**: Match voice personality to speaker role
3. **Use style prompts**: Add emotional context in dialogue
4. **Test webhooks**: Use webhook.site for development testing
5. **Monitor usage**: Track Google API quota consumption 