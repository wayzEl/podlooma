#!/bin/bash
# Cloudflare Pages Deployment Script

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