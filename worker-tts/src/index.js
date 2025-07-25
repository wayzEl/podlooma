// Cloudflare Worker for Asynchronous TTS Processing
export default {
  async fetch(request, env, ctx) {
    try {
      const url = new URL(request.url);
      
      // Handle CORS preflight
      if (request.method === 'OPTIONS') {
        return new Response(null, {
          status: 200,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
          },
        });
      }

      // Only handle POST requests to /tts-process
      if (request.method !== 'POST' || url.pathname !== '/tts-process') {
        return new Response(JSON.stringify({ 
          error: 'Not Found',
          message: 'This Worker only handles POST requests to /tts-process'
        }), {
          status: 404,
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }

      // Parse the TTS job request
      const jobData = await request.json();
      const { 
        job_id, 
        dialogue, 
        voices, 
        model, 
        webhook_url, 
        episode_id,
        audio_url 
      } = jobData;

      console.log(`🚀 Worker starting TTS processing for job ${job_id}`);

      // Get API key from environment secrets
      const api_key = env.GOOGLE_API_KEY;
      if (!api_key) {
        console.error('GOOGLE_API_KEY not configured in Worker environment');
        return new Response(JSON.stringify({
          error: 'Configuration Error',
          message: 'API key not configured'
        }), {
          status: 500,
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }

      // Use waitUntil to ensure background processing completes
      ctx.waitUntil(
        processTTSJob({
          job_id,
          dialogue,
          voices,
          model,
          api_key,
          webhook_url,
          episode_id,
          audio_url,
          env
        })
      );

      // Return immediate acknowledgment
      return new Response(JSON.stringify({
        status: 'accepted',
        job_id: job_id,
        message: 'TTS job accepted for processing'
      }), {
        status: 200,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });

    } catch (error) {
      console.error('Worker error:', error);
      return new Response(JSON.stringify({
        error: 'Internal Worker Error',
        message: error.message
      }), {
        status: 500,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }
  }
};

// TTS Job Processing Function
async function processTTSJob({ job_id, dialogue, voices, model, api_key, webhook_url, episode_id, audio_url, env }) {
  try {
    console.log(`🎯 Processing TTS job ${job_id}`);

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
      await sendWebhook(webhook_url, {
        episode_id: episode_id,
        status: "failed",
        error: `Google API error: ${googleResponse.status} - ${errorText}`,
        job_id: job_id,
        timestamp: new Date().toISOString()
      });

      throw new Error(`Google API error: ${googleResponse.status} - ${errorText}`);
    }

    const ttsResponse = await googleResponse.json();
    
    // Extract audio data
    const audioData = ttsResponse.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    
    if (!audioData) {
      console.log('No audio data found in Google TTS response');
      
      // Send failure webhook
      await sendWebhook(webhook_url, {
        episode_id: episode_id,
        status: "failed",
        error: "No audio data in response from Google TTS API",
        job_id: job_id,
        timestamp: new Date().toISOString()
      });

      throw new Error("No audio data in response from Google TTS API");
    }

    // Store the audio data in KV for retrieval
    if (env.AUDIO_FILES) {
      await env.AUDIO_FILES.put(job_id, audioData, {
        expirationTtl: 86400 // Expire after 24 hours
      });
      console.log(`✅ Audio stored in KV for job ${job_id}`);
    } else {
      console.warn('AUDIO_FILES KV namespace not configured');
      throw new Error('Audio storage not configured');
    }

    // Send SUCCESS webhook notification
    const webhookPayload = {
      episode_id: episode_id,
      status: "completed",
      audio_url: audio_url,
      job_id: job_id,
      timestamp: new Date().toISOString()
    };

    console.log(`🔔 Sending success webhook for job ${job_id}`);
    
    await sendWebhook(webhook_url, webhookPayload);

    console.log(`🎉 TTS job ${job_id} completed successfully`);

  } catch (error) {
    console.error(`TTS job ${job_id} failed:`, error);
    
    // Send failure webhook for processing errors
    try {
      await sendWebhook(webhook_url, {
        episode_id: episode_id,
        status: "failed",
        error: error.message,
        job_id: job_id,
        timestamp: new Date().toISOString()
      });
    } catch (webhookError) {
      console.error(`Failed to send failure webhook for job ${job_id}:`, webhookError);
    }
  }
}

// Helper function to send webhooks
async function sendWebhook(webhook_url, payload) {
  try {
    const webhookResponse = await fetch(webhook_url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (webhookResponse.ok) {
      console.log(`✅ Webhook sent successfully for job ${payload.job_id}`);
    } else {
      console.error(`❌ Webhook failed for job ${payload.job_id}: ${webhookResponse.status}`);
      throw new Error(`Webhook HTTP ${webhookResponse.status}`);
    }
  } catch (err) {
    console.error(`❌ Webhook error for job ${payload.job_id}:`, err);
    throw err;
  }
} 