// Cloudflare Pages Function to serve audio files
export async function onRequestGet({ params, env }) {
  try {
    const audioId = params.id;
    
    if (!audioId) {
      return new Response("Audio ID required", { status: 400 });
    }

    // Retrieve audio data from KV
    if (!env.AUDIO_FILES) {
      return new Response("Storage not configured", { status: 500 });
    }

    const audioData = await env.AUDIO_FILES.get(audioId);
    
    if (!audioData) {
      return new Response("Audio file not found", { status: 404 });
    }

    // Convert base64 to binary
    const audioBuffer = Uint8Array.from(atob(audioData), c => c.charCodeAt(0));

    return new Response(audioBuffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/wav",
        "Content-Disposition": `attachment; filename="${audioId}.wav"`,
        "Access-Control-Allow-Origin": "*"
      }
    });

  } catch (error) {
    console.error('Audio serving error:', error);
    return new Response("Internal server error", { status: 500 });
  }
} 