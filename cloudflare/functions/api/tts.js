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
    const audioUrl = `https://${request.headers.get('host')}/api/audio/${jobId}`;

    console.log(`🔄 Starting TTS processing for job ${jobId}`);

    // Start background processing (fire and forget)
    processTTSAsync(jobId, audioUrl, dialogue, voices, model, api_key, webhook_url, episode_id, env)
      .catch(error => {
        console.error(`Background TTS processing failed for job ${jobId}:`, error);
      });

    // Return immediate response with job ID
    return new Response(JSON.stringify({
      status: "processing",
      job_id: jobId,
      message: "TTS generation started. You will receive a webhook when complete.",
      audio_url: audioUrl,
      timestamp: new Date().toISOString()
    }), {
      status: 202, // 202 Accepted
      headers: { 
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });

  } catch (error) {
    console.error('TTS Error:', error);
    
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

// Background TTS processing function
async function processTTSAsync(jobId, audioUrl, dialogue, voices, model, api_key, webhook_url, episode_id, env) {
  try {
    // Build speaker voice configurations
    const speakerVoiceConfigs = Object.entries(voices).map(([speaker, voice]) => ({
      speaker: speaker,
      voiceConfig: {
        prebuiltVoiceConfig: {
          voiceName: voice
        }
      }
    }));

    // Determine if this is single or multi-speaker
    const isSingleSpeaker = speakerVoiceConfigs.length === 1;
    const isMultiSpeaker = speakerVoiceConfigs.length >= 2;

    // Build the appropriate request format
    let ttsRequest;
    
    if (isSingleSpeaker) {
      // For single speaker, use standard TTS format (not multi-speaker)
      ttsRequest = {
        contents: [{ 
          parts: [{ text: dialogue }] 
        }],
        generationConfig: {
          responseModalities: ["AUDIO"],
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: {
                voiceName: speakerVoiceConfigs[0].voiceConfig.prebuiltVoiceConfig.voiceName
              }
            }
          }
        }
      };
    } else if (isMultiSpeaker) {
      // For multi-speaker, use multi-speaker format
      ttsRequest = {
        contents: [{ 
          parts: [{ text: dialogue }] 
        }],
        generationConfig: {
          responseModalities: ["AUDIO"],
          speechConfig: {
            multiSpeakerVoiceConfig: {
              speakerVoiceConfigs: speakerVoiceConfigs
            }
          }
        }
      };
    } else {
      throw new Error("At least one voice must be specified");
    }

    console.log(`Using ${isSingleSpeaker ? 'single' : 'multi'}-speaker TTS with ${speakerVoiceConfigs.length} voice(s)`);
    console.log('Sending TTS request:', JSON.stringify(ttsRequest, null, 2));

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

    console.log('Google API Response Status:', googleResponse.status);
    console.log('Google API Response Headers:', [...googleResponse.headers.entries()]);

    if (!googleResponse.ok) {
      const errorText = await googleResponse.text();
      console.log('Google API Error Response:', errorText);
      
      // Send failure webhook
      const failurePayload = {
        episode_id: episode_id,
        status: "failed",
        error: `Google API error: ${googleResponse.status} - ${errorText}`,
        job_id: jobId,
        timestamp: new Date().toISOString()
      };

      // Send failure webhook (don't await)
      fetch(webhook_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(failurePayload)
      }).catch(err => console.error('Failure webhook error:', err));

      throw new Error(`Google API error: ${googleResponse.status} - ${errorText}`);
    }

    const ttsResponse = await googleResponse.json();
    
    // Extract audio data
    const audioData = ttsResponse.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    
    if (!audioData) {
      console.log('No audio data found in Google TTS response');
      
      // Send failure webhook
      const failurePayload = {
        episode_id: episode_id,
        status: "failed",
        error: "No audio data in response from Google TTS API",
        job_id: jobId,
        timestamp: new Date().toISOString()
      };

      // Send failure webhook (don't await)
      fetch(webhook_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(failurePayload)
      }).catch(err => console.error('Failure webhook error:', err));

      throw new Error("No audio data in response from Google TTS API");
    }

    // Store the audio data in KV for retrieval
    if (env.AUDIO_FILES) {
      await env.AUDIO_FILES.put(jobId, audioData, {
        expirationTtl: 86400 // Expire after 24 hours
      });
      console.log(`✅ Audio stored in KV for job ${jobId}`);
    } else {
      console.warn('AUDIO_FILES KV namespace not configured');
      throw new Error('Audio storage not configured');
    }

    // Send SUCCESS webhook notification
    const webhookPayload = {
      episode_id: episode_id,
      status: "completed",
      audio_url: audioUrl,
      job_id: jobId,
      timestamp: new Date().toISOString()
    };

    console.log(`🔔 Sending success webhook for job ${jobId}`);
    
    try {
      const webhookResponse = await fetch(webhook_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(webhookPayload)
      });

      if (webhookResponse.ok) {
        console.log(`✅ Success webhook sent for job ${jobId}`);
      } else {
        console.error(`❌ Webhook failed for job ${jobId}: ${webhookResponse.status}`);
      }
    } catch (err) {
      console.error(`❌ Webhook error for job ${jobId}:`, err);
    }

  } catch (error) {
    console.error(`Background TTS processing error for job ${jobId}:`, error);
    
    // Send failure webhook for background processing errors
    try {
      const failurePayload = {
        episode_id: episode_id,
        status: "failed",
        error: error.message,
        job_id: jobId,
        timestamp: new Date().toISOString()
      };

      const webhookResponse = await fetch(webhook_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(failurePayload)
      });

      if (webhookResponse.ok) {
        console.log(`✅ Failure webhook sent for job ${jobId}`);
      } else {
        console.error(`❌ Failure webhook failed for job ${jobId}`);
      }
    } catch (webhookError) {
      console.error(`❌ Failed to send failure webhook for job ${jobId}:`, webhookError);
    }
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