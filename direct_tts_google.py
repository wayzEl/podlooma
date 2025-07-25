#!/usr/bin/env python3
"""
Direct TTS using Google's documented API pattern - bypasses worker entirely
"""
import os
import wave
import subprocess
from google import genai
from google.genai import types

# Set up the wave file to save the output (from Google docs):
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def generate_single_speaker():
    """Generate single speaker TTS audio"""
    print("🎤 SINGLE SPEAKER TTS")
    print("=" * 30)
    
    client = genai.Client()
    
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents="Say cheerfully: Welcome to our amazing text-to-speech demonstration! This technology is absolutely incredible and sounds so natural!",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Kore',  # Firm voice
                    )
                )
            ),
        )
    )
    
    data = response.candidates[0].content.parts[0].inline_data.data
    
    filename = 'single_speaker.wav'
    wave_file(filename, data)
    
    print(f"✅ Generated: {filename}")
    return filename

def generate_multi_speaker():
    """Generate multi-speaker TTS audio"""
    print("\n🎭 MULTI-SPEAKER TTS")
    print("=" * 30)
    
    client = genai.Client()
    
    prompt = """TTS the following conversation between Sarah and Alex:
    
Sarah: Hi everyone! Welcome to our podcast about artificial intelligence. I'm Sarah, your host.

Alex: And I'm Alex! Thanks for having me on, Sarah. I'm really excited to talk about how AI is changing everything.

Sarah: Alex, what's the most impressive AI development you've seen recently?

Alex: Oh wow, definitely text-to-speech technology! The voices are getting so realistic, like what we're using right now!

Sarah: Absolutely! It's amazing how natural this sounds. Our listeners are going to be blown away!

Alex: The future of AI communication is here, and it's incredible!"""
    
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(
                            speaker='Sarah',
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name='Kore',  # Firm
                                )
                            )
                        ),
                        types.SpeakerVoiceConfig(
                            speaker='Alex',
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name='Puck',  # Upbeat
                                )
                            )
                        ),
                    ]
                )
            )
        )
    )
    
    data = response.candidates[0].content.parts[0].inline_data.data
    
    filename = 'multi_speaker.wav'
    wave_file(filename, data)
    
    print(f"✅ Generated: {filename}")
    return filename

def generate_styled_speech():
    """Generate speech with specific style prompts"""
    print("\n🎨 STYLED SPEECH TTS")
    print("=" * 30)
    
    client = genai.Client()
    
    prompt = """Make Speaker1 sound excited and energetic, and Speaker2 sound calm and wise:

Speaker1: Oh my goodness! This is absolutely incredible! The quality is amazing!

Speaker2: Indeed, the advancement in artificial intelligence continues to astound us all. The technology has matured beautifully."""
    
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(
                            speaker='Speaker1',
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name='Fenrir',  # Excitable
                                )
                            )
                        ),
                        types.SpeakerVoiceConfig(
                            speaker='Speaker2',
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name='Gacrux',  # Mature
                                )
                            )
                        ),
                    ]
                )
            )
        )
    )
    
    data = response.candidates[0].content.parts[0].inline_data.data
    
    filename = 'styled_speech.wav'
    wave_file(filename, data)
    
    print(f"✅ Generated: {filename}")
    return filename

def play_audio_files(filenames):
    """Play all generated audio files"""
    print(f"\n🔊 PLAYING AUDIO FILES")
    print("=" * 35)
    
    for filename in filenames:
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"\n🎵 Playing: {filename}")
            print(f"   Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            try:
                # Play audio
                subprocess.run(["afplay", filename], check=True)
                print(f"   ✅ Playback completed")
            except Exception as e:
                print(f"   ⚠️ Playback failed: {e}")
                print(f"   💡 Try: open {filename}")
        else:
            print(f"❌ File not found: {filename}")

if __name__ == "__main__":
    print("🎙️ DIRECT GOOGLE TTS GENERATION")
    print("=" * 45)
    print("Using Google's documented API pattern")
    print("Bypassing worker queue entirely")
    
    # Set API key
    os.environ['GOOGLE_API_KEY'] = 'AIzaSyDN8Uf0G0T0pJNzHgm5265zPoflCP_DjMs'
    
    generated_files = []
    
    try:
        # Generate different types of audio
        file1 = generate_single_speaker()
        generated_files.append(file1)
        
        file2 = generate_multi_speaker()
        generated_files.append(file2)
        
        file3 = generate_styled_speech()
        generated_files.append(file3)
        
        # Play all generated audio
        play_audio_files(generated_files)
        
        print(f"\n🎉 SUCCESS! Generated {len(generated_files)} audio files:")
        for filename in generated_files:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                print(f"   📁 {filename} ({size:,} bytes)")
        
        print(f"\n💡 These files should have actual audio content!")
        print(f"   You can play them with: afplay <filename>")
        print(f"   Or open them with: open <filename>")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc() 