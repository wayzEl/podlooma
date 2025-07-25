// Cloudflare Pages Function for TTS Generation
export async function onRequestPost({ request, env }) {
  try {
    // Parse the incoming request
    const body = await request.json();
    const { dialogue, voices, model, api_key, webhook_url, episode_id } = body;

    // Validate required fields
    if (!dialogue || !voices || !model || !api_key || !webhook_url || !episode_id) {
      return new Response(JSON.stringify({ 
        error: "Missing required fields",
        required: ["dialogue", "voices", "model", "api_key", "webhook_url", "episode_id"]
      }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
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
      throw new Error("No audio data in response");
    }

    // Store audio in Cloudflare KV or R2 (for this demo, we'll use a simple storage approach)
    // In production, you'd want to use R2 for file storage
    const audioUrl = `https://${request.headers.get('host')}/api/audio/${jobId}`;

    // Store the audio data in KV for retrieval
    if (env.AUDIO_FILES) {
      await env.AUDIO_FILES.put(jobId, audioData);
    }

    // Send webhook notification
    const webhookPayload = {
      episode_id: episode_id,
      status: "success",
      audio_url: audioUrl
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
      audio_url: audioUrl
    }), {
      status: 200,
      headers: { 
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });

  } catch (error) {
    console.error('TTS Error:', error);
    
    // Send failure webhook if possible
    if (body?.webhook_url && body?.episode_id) {
      fetch(body.webhook_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          episode_id: body.episode_id,
          status: "failed",
          error: error.message
        })
      }).catch(() => {});
    }

    return new Response(JSON.stringify({
      error: error.message
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