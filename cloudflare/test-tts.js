// Enhanced test script to properly test Google TTS API with detailed tracking
// Usage: node test-tts.js YOUR_GOOGLE_API_KEY

const apiKey = process.argv[2];

if (!apiKey) {
  console.log('Usage: node test-tts.js YOUR_GOOGLE_API_KEY');
  process.exit(1);
}

async function testTTS() {
  console.log('🚀 Starting TTS Test with Real Details...\n');
  
  // Test Case 1: Single Speaker (should use standard format)
  await testSingleSpeaker();
  
  console.log('\n' + '='.repeat(60) + '\n');
  
  // Test Case 2: Multi Speaker (should use multi-speaker format)
  await testMultiSpeaker();
}

async function testSingleSpeaker() {
  console.log('📋 TEST CASE 1: Single Speaker');
  console.log('================================');
  
  const dialogue = "This is a test of the single speaker TTS functionality. The voice should be clear and natural.";
  const voices = { "Speaker 1": "Kore" };
  const model = "gemini-2.5-flash-preview-tts";

  // Build speaker voice configurations
  const speakerVoiceConfigs = Object.entries(voices).map(([speaker, voice]) => ({
    speaker: speaker,
    voiceConfig: {
      prebuiltVoiceConfig: {
        voiceName: voice
      }
    }
  }));

  // Use SINGLE speaker format (not multi-speaker)
  const ttsRequest = {
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

  console.log('📝 Input Details:');
  console.log(`   Dialogue: "${dialogue}"`);
  console.log(`   Voices: ${JSON.stringify(voices)}`);
  console.log(`   Model: ${model}`);
  console.log(`   Format: Single Speaker (standard TTS)`);
  console.log('\n📤 Request Payload:', JSON.stringify(ttsRequest, null, 2));

  await makeRequest(ttsRequest, model, "Single Speaker");
}

async function testMultiSpeaker() {
  console.log('📋 TEST CASE 2: Multi Speaker');
  console.log('==============================');
  
  const dialogue = "Speaker 1: Hello there! How are you doing today? Speaker 2: I'm doing great, thank you for asking! How about you?";
  const voices = { 
    "Speaker 1": "Kore", 
    "Speaker 2": "Charon" 
  };
  const model = "gemini-2.5-flash-preview-tts";

  // Build speaker voice configurations
  const speakerVoiceConfigs = Object.entries(voices).map(([speaker, voice]) => ({
    speaker: speaker,
    voiceConfig: {
      prebuiltVoiceConfig: {
        voiceName: voice
      }
    }
  }));

  // Use MULTI speaker format
  const ttsRequest = {
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

  console.log('📝 Input Details:');
  console.log(`   Dialogue: "${dialogue}"`);
  console.log(`   Voices: ${JSON.stringify(voices)}`);
  console.log(`   Model: ${model}`);
  console.log(`   Format: Multi Speaker (${speakerVoiceConfigs.length} speakers)`);
  console.log('\n📤 Request Payload:', JSON.stringify(ttsRequest, null, 2));

  await makeRequest(ttsRequest, model, "Multi Speaker");
}

async function makeRequest(ttsRequest, model, testType) {
  const startTime = Date.now();
  
  try {
    console.log(`\n🔄 Making ${testType} API Request...`);
    
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(ttsRequest)
      }
    );

    const endTime = Date.now();
    const responseTime = endTime - startTime;

    console.log('\n📊 Response Details:');
    console.log(`   Status: ${response.status} ${response.statusText}`);
    console.log(`   Response Time: ${responseTime}ms`);
    console.log('   Headers:');
    for (const [key, value] of response.headers.entries()) {
      console.log(`     ${key}: ${value}`);
    }

    if (!response.ok) {
      const errorText = await response.text();
      console.log('\n❌ Error Response Body:', errorText);
      console.log(`\n🚨 ${testType} Test FAILED`);
      return;
    }

    const data = await response.json();
    console.log('\n📦 Response Structure:');
    console.log(`   Candidates: ${data.candidates?.length || 0}`);
    console.log(`   Usage Metadata: ${JSON.stringify(data.usageMetadata || {})}`);

    // Check for audio data
    const audioData = data.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    const mimeType = data.candidates?.[0]?.content?.parts?.[0]?.inlineData?.mimeType;
    
    if (audioData) {
      console.log('\n🎵 Audio Data Found:');
      console.log(`   MIME Type: ${mimeType}`);
      console.log(`   Data Length: ${audioData.length} characters`);
      console.log(`   Estimated Size: ~${Math.round(audioData.length * 0.75 / 1024)} KB`);
      console.log(`   First 50 chars: ${audioData.substring(0, 50)}...`);
      console.log(`\n✅ ${testType} Test SUCCESSFUL`);
    } else {
      console.log('\n❌ No audio data found in response');
      console.log('Full response:', JSON.stringify(data, null, 2));
      console.log(`\n🚨 ${testType} Test FAILED - No Audio Data`);
    }

  } catch (error) {
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    console.log(`\n💥 Network/Parse Error (after ${responseTime}ms):`, error.message);
    console.log(`\n🚨 ${testType} Test FAILED - Network Error`);
  }
}

// Run the tests
testTTS().then(() => {
  console.log('\n🏁 All tests completed!');
}).catch(error => {
  console.error('\n💥 Test suite failed:', error);
  process.exit(1);
}); 