// Cloudflare Pages Function for TTS Generation
export async function onRequestPost({ request, env }) {
  let requestBody = null;
  
  try {
    // Parse the incoming request
    requestBody = await request.json();
    const { dialogue, voices, model, api_key, webhook_url, episode_id } = requestBody;

    // Validate required fields
    if (!dialogue || !voices || !model || !api_key || !webhook_url || !episode_id) {
      return new Response(JSON.stringify({ 
        error: "Missing required fields",
        required: ["dialogue", "voices", "model", "api_key", "webhook_url", "episode_id"]
      }), {
        status: 400,
        headers: { 
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // Validate dialogue length (Google TTS has limits)
    if (dialogue.length > 5000) {
      return new Response(JSON.stringify({ 
        error: "Dialogue too long. Maximum 5000 characters.",
        current_length: dialogue.length
      }), {
        status: 400,
        headers: { 
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // Validate voices object
    if (typeof voices !== 'object' || Object.keys(voices).length === 0) {
      return new Response(JSON.stringify({ 
        error: "Invalid voices configuration. Must be an object with speaker names as keys."
      }), {
        status: 400,
        headers: { 
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // Generate unique job ID
    const jobId = crypto.randomUUID();

    // Build the Google TTS request
    const speakerVoiceConfigs = Object.entries(voices).map(([speaker, voice]) => ({
      speaker: speaker,
      voiceConfig: {
        prebuiltVoiceConfig: {
          voiceName: voice
        }
      }
    }));

    const ttsRequest = {
      model: model,
      contents: [{ parts: [{ text: dialogue }] }],
      generationConfig: {
        responseModalities: ["AUDIO"],
        speechConfig: {
          multiSpeakerVoiceConfig: {
            speakerVoiceConfigs: speakerVoiceConfigs
          }
        }
      }
    };

    // Call Google TTS API
    const googleResponse = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${api_key}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(ttsRequest)
      }
    );

    if (!googleResponse.ok) {
      const errorText = await googleResponse.text();
      throw new Error(`Google API error: ${googleResponse.status} - ${errorText}`);
    }

    const ttsResponse = await googleResponse.json();
    
    // Extract audio data
    const audioData = ttsResponse.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    
    if (!audioData) {
      throw new Error("No audio data in response from Google TTS API");
    }

    // Store audio in Cloudflare KV
    const audioUrl = `https://${request.headers.get('host')}/api/audio/${jobId}`;

    // Store the audio data in KV for retrieval
    if (env.AUDIO_FILES) {
      await env.AUDIO_FILES.put(jobId, audioData, {
        expirationTtl: 86400 // Expire after 24 hours
      });
    } else {
      console.warn('AUDIO_FILES KV namespace not configured');
    }

    // Send webhook notification
    const webhookPayload = {
      episode_id: episode_id,
      status: "success",
      audio_url: audioUrl,
      job_id: jobId,
      timestamp: new Date().toISOString()
    };

    // Send webhook asynchronously (don't wait for it)
    fetch(webhook_url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(webhookPayload)
    }).catch(err => console.error('Webhook error:', err));

    // Return immediate response
    return new Response(JSON.stringify({
      status: "completed",
      job_id: jobId,
      audio_url: audioUrl,
      timestamp: new Date().toISOString()
    }), {
      status: 200,
      headers: { 
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });

  } catch (error) {
    console.error('TTS Error:', error);
    
    // Send failure webhook if possible and request body was parsed
    if (requestBody?.webhook_url && requestBody?.episode_id) {
      fetch(requestBody.webhook_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          episode_id: requestBody.episode_id,
          status: "failed",
          error: error.message,
          timestamp: new Date().toISOString()
        })
      }).catch(() => {
        // Silently fail webhook on error
      });
    }

    return new Response(JSON.stringify({
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

// Handle CORS preflight
export async function onRequestOptions() {
  return new Response(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
} 