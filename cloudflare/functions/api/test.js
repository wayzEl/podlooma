// Simple test function to verify Functions are working
export async function onRequestGet() {
  return new Response(JSON.stringify({
    message: "🎉 Cloudflare Pages Functions are working!",
    timestamp: new Date().toISOString(),
    endpoints: {
      tts: "POST /api/tts",
      audio: "GET /api/audio/:id",
      test: "GET /api/test (this endpoint)"
    }
  }), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"
    }
  });
} 