#!/bin/bash
# Cloudflare Pages Deployment Script for Podlooma TTS

echo "🚀 Deploying Podlooma TTS to Cloudflare Pages..."

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "📦 Installing Wrangler CLI..."
    npm install -g wrangler
fi

# Login to Cloudflare (if not already logged in)
echo "🔐 Checking Cloudflare authentication..."
wrangler whoami || wrangler login

# Deploy to Cloudflare Pages
echo "🌍 Deploying to Cloudflare Pages..."
wrangler pages deploy . --project-name podlooma-tts

echo "✅ Deployment complete!"
echo "🌐 Your TTS API will be available at: https://podlooma-tts.pages.dev"
echo ""
echo "🔧 Next step: Create KV namespace for audio storage"
echo "   Run: wrangler kv:namespace create \"AUDIO_FILES\""
echo "   Then bind it in Cloudflare Pages Settings → Functions"
echo ""
echo "✨ No environment variables needed - users provide their own API keys!" 