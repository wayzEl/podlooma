#!/bin/bash
# Cloudflare Pages Deployment Script for Podlooma

echo "🚀 Deploying Podlooma to Cloudflare Pages..."

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "📦 Installing Wrangler CLI..."
    npm install -g wrangler
fi

# Login to Cloudflare (if not already logged in)
echo "🔐 Checking Cloudflare authentication..."
wrangler whoami || wrangler login

# Create KV namespace for audio storage if it doesn't exist
echo "🗄️ Setting up KV namespace for audio storage..."
echo "Creating AUDIO_FILES KV namespace..."
wrangler kv namespace create "AUDIO_FILES" || echo "KV namespace may already exist"

echo "Creating preview AUDIO_FILES KV namespace..."
wrangler kv namespace create "AUDIO_FILES" --preview || echo "Preview KV namespace may already exist"

# Deploy to Cloudflare Pages
echo "🌍 Deploying to Cloudflare Pages..."
wrangler pages deploy cloudflare --project-name podlooma

echo "✅ Deployment complete!"
echo ""
echo "🌐 Your TTS API will be available at: https://podlooma.pages.dev"
echo ""
echo "🔧 Important Next Steps:"
echo "   1. Go to Cloudflare Dashboard → Pages → podlooma → Settings → Functions"
echo "   2. Add KV namespace binding:"
echo "      - Variable name: AUDIO_FILES"
echo "      - KV namespace: Select the 'AUDIO_FILES' namespace created above"
echo ""
echo "🔑 Optional Environment Variables (Set in Pages Settings → Environment variables):"
echo "   - GOOGLE_API_KEY: Your Google API key (can also be provided per request)"
echo ""
echo "✅ Test your deployment:"
echo "   GET  https://podlooma.pages.dev/api/test"
echo "   POST https://podlooma.pages.dev/api/tts"
echo ""
echo "✨ Ready to generate multi-speaker TTS audio!" 