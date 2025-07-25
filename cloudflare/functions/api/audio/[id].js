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

    // Convert base64 to binary (PCM data from Google TTS)
    let pcmData;
    try {
      pcmData = Uint8Array.from(atob(audioData), c => c.charCodeAt(0));
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

    // Convert PCM to WAV format
    // Google TTS returns 16-bit Linear PCM at 24kHz
    const wavBuffer = pcmToWav(pcmData, 24000, 16, 1);

    // Determine if this is a download request
    const userAgent = request.headers.get('User-Agent') || '';
    const isDownload = request.url.includes('download=true') || 
                      userAgent.includes('curl') || 
                      userAgent.includes('wget');

    // Return audio file with appropriate headers
    return new Response(wavBuffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/wav",
        "Content-Length": wavBuffer.length.toString(),
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

// Convert PCM data to WAV format
function pcmToWav(pcmData, sampleRate, bitsPerSample, numChannels) {
  const blockAlign = numChannels * bitsPerSample / 8;
  const byteRate = sampleRate * blockAlign;
  const dataSize = pcmData.length;
  const fileSize = 36 + dataSize;

  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  // RIFF chunk descriptor
  const writeString = (offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  writeString(0, 'RIFF');                    // ChunkID
  view.setUint32(4, fileSize, true);        // ChunkSize (little-endian)
  writeString(8, 'WAVE');                   // Format

  // fmt sub-chunk
  writeString(12, 'fmt ');                  // Subchunk1ID
  view.setUint32(16, 16, true);             // Subchunk1Size (16 for PCM)
  view.setUint16(20, 1, true);              // AudioFormat (1 for PCM)
  view.setUint16(22, numChannels, true);    // NumChannels
  view.setUint32(24, sampleRate, true);     // SampleRate
  view.setUint32(28, byteRate, true);       // ByteRate
  view.setUint16(32, blockAlign, true);     // BlockAlign
  view.setUint16(34, bitsPerSample, true);  // BitsPerSample

  // data sub-chunk
  writeString(36, 'data');                  // Subchunk2ID
  view.setUint32(40, dataSize, true);       // Subchunk2Size

  // Copy PCM data
  const uint8View = new Uint8Array(buffer);
  uint8View.set(pcmData, 44);

  return uint8View;
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