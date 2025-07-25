// Simple test function to verify Functions are working
export async function onRequestGet({ env, request }) {
  try {
    // Check environment configuration
    const envChecks = {
      audio_storage: !!env.AUDIO_FILES,
      google_api_key: !!env.GOOGLE_API_KEY,
      host: request.headers.get('host'),
      user_agent: request.headers.get('user-agent'),
    };

    // Get available voice list for testing
    const availableVoices = [
      'Kore', 'Puck', 'Zephyr', 'Fenrir', 'Gacrux', 'Enceladus',
      'Orus', 'Aoede', 'Autonoe', 'Umbriel', 'Algieba', 'Algenib',
      'Erinome', 'Laomedeia', 'Schedar', 'Achird', 'Zubenelgenubi',
      'Sadachbia', 'Sadaltager', 'Achernar'
    ];

    return new Response(JSON.stringify({
      status: "operational",
      message: "🎉 Cloudflare Pages Functions are working!",
      timestamp: new Date().toISOString(),
      version: "1.0.0",
      environment: {
        checks: envChecks,
        warnings: [
          ...(!envChecks.audio_storage ? ["AUDIO_FILES KV namespace not configured"] : []),
          ...(!envChecks.google_api_key ? ["GOOGLE_API_KEY environment variable not set"] : [])
        ]
      },
      endpoints: {
        test: {
          method: "GET",
          path: "/api/test",
          description: "Health check and system status"
        },
        tts: {
          method: "POST", 
          path: "/api/tts",
          description: "Generate TTS audio from dialogue",
          required_fields: ["dialogue", "voices", "model", "api_key", "webhook_url", "episode_id"]
        },
        audio: {
          method: "GET",
          path: "/api/audio/:id",
          description: "Retrieve generated audio file by ID"
        }
      },
      available_voices: availableVoices,
      example_request: {
        url: `/api/tts`,
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: {
          dialogue: "Speaker 1: Hello!\nSpeaker 2: Hi there!",
          voices: {
            "Speaker 1": "Kore",
            "Speaker 2": "Puck"
          },
          model: "gemini-2.5-flash-preview-tts",
          api_key: "your-google-api-key",
          webhook_url: "https://webhook.site/your-unique-url",
          episode_id: "test-episode-001"
        }
      }
    }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache"
      }
    });

  } catch (error) {
    console.error('Test endpoint error:', error);
    return new Response(JSON.stringify({
      status: "error",
      message: "Test endpoint encountered an error",
      error: error.message,
      timestamp: new Date().toISOString()
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });
  }
}

// Handle CORS preflight for test endpoint
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