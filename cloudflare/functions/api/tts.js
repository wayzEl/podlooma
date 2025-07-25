// Cloudflare Pages Function for TTS Generation - Worker Trigger
export async function onRequestPost({ request, env }) {
  try {
    // Parse the incoming request
    const requestBody = await request.json();
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

    console.log(`🚀 Triggering Worker for TTS job ${jobId}`);

    // Prepare job data for Worker
    const jobData = {
      job_id: jobId,
      dialogue,
      voices,
      model,
      webhook_url,
      episode_id,
      audio_url: audioUrl
    };

    // Trigger the Worker asynchronously
    const workerUrl = 'https://podlooma-tts-worker.lunanipersonal.workers.dev/tts-process';
    
    try {
      const workerResponse = await fetch(workerUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jobData)
      });

      if (!workerResponse.ok) {
        const errorText = await workerResponse.text();
        console.error('Worker trigger failed:', workerResponse.status, errorText);
        throw new Error(`Worker failed to accept job: ${workerResponse.status}`);
      }

      console.log(`✅ Worker accepted TTS job ${jobId}`);
    } catch (workerError) {
      console.error('Failed to trigger Worker:', workerError);
      
      // Send immediate failure webhook since Worker couldn't be triggered
      try {
        await fetch(webhook_url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            episode_id: episode_id,
            status: "failed",
            error: `Failed to trigger TTS processing: ${workerError.message}`,
            job_id: jobId,
            timestamp: new Date().toISOString()
          })
        });
      } catch (webhookError) {
        console.error('Failed to send failure webhook:', webhookError);
      }
      
      throw workerError;
    }

    // Return immediate response
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
    console.error('TTS Trigger Error:', error);
    
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