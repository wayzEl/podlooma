// Cloudflare Pages Function to serve audio files
export async function onRequestGet({ params, env, request }) {
  try {
    const audioId = params.id;
    
    // Validate audio ID parameter
    if (!audioId) {
      return new Response(JSON.stringify({
        error: "Audio ID required",
        message: "Please provide a valid audio ID in the URL path"
      }), { 
        status: 400,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // Validate audio ID format (should be UUID)
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(audioId)) {
      return new Response(JSON.stringify({
        error: "Invalid audio ID format",
        message: "Audio ID must be a valid UUID"
      }), { 
        status: 400,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // Check if KV storage is configured
    if (!env.AUDIO_FILES) {
      console.error('AUDIO_FILES KV namespace not configured');
      return new Response(JSON.stringify({
        error: "Storage not configured",
        message: "Audio storage service is not properly configured"
      }), { 
        status: 500,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // Retrieve audio data from KV
    const audioData = await env.AUDIO_FILES.get(audioId);
    
    if (!audioData) {
      return new Response(JSON.stringify({
        error: "Audio file not found",
        message: `No audio file found with ID: ${audioId}. The file may have expired or never existed.`
      }), { 
        status: 404,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // Convert base64 to binary
    let audioBuffer;
    try {
      audioBuffer = Uint8Array.from(atob(audioData), c => c.charCodeAt(0));
    } catch (decodeError) {
      console.error('Base64 decode error:', decodeError);
      return new Response(JSON.stringify({
        error: "Audio file corrupted",
        message: "The audio file data is corrupted and cannot be decoded"
      }), { 
        status: 500,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // Determine if this is a download request
    const userAgent = request.headers.get('User-Agent') || '';
    const isDownload = request.url.includes('download=true') || 
                      userAgent.includes('curl') || 
                      userAgent.includes('wget');

    // Return audio file with appropriate headers
    return new Response(audioBuffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/wav",
        "Content-Length": audioBuffer.length.toString(),
        "Content-Disposition": isDownload 
          ? `attachment; filename="${audioId}.wav"` 
          : `inline; filename="${audioId}.wav"`,
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "public, max-age=3600", // Cache for 1 hour
        "Last-Modified": new Date().toUTCString()
      }
    });

  } catch (error) {
    console.error('Audio serving error:', error);
    return new Response(JSON.stringify({
      error: "Internal server error",
      message: "An unexpected error occurred while retrieving the audio file"
    }), { 
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });
  }
}

// Handle CORS preflight for audio endpoint
export async function onRequestOptions() {
  return new Response(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
} 