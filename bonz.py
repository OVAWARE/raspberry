import os
import requests
import json
import time
from gtts import gTTS
import tempfile
import platform
import subprocess
import numpy as np
import torch
from openai import whisper
import sounddevice as sd
import soundfile as sf
import wave

def listen_for_wake_word(wake_word="bonz", timeout=None):
    """Listen for the wake word using whisper-tiny model"""
    print(f"Listening for wake word: '{wake_word}'...")
    
    # Load the tiny model for wake word detection
    model_tiny = whisper.load_model("tiny")
    
    # Audio parameters
    RATE = 16000
    CHANNELS = 1
    DURATION = 2  # Listen for 2 seconds at a time
    
    start_time = time.time()
    
    # Listen for 2 seconds at a time to check for wake word
    while True:
        if timeout and (time.time() - start_time) > timeout:
            return False
        
        # Record audio for DURATION seconds
        print("Listening...")
        recording = sd.rec(int(DURATION * RATE), samplerate=RATE, channels=CHANNELS, dtype='float32')
        sd.wait()  # Wait until recording is finished
        
        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
            temp_filename = temp_wav.name
        
        sf.write(temp_filename, recording, RATE, 'PCM_16')
        
        # Transcribe with whisper tiny
        result = model_tiny.transcribe(temp_filename)
        transcription = result["text"].lower().strip()
        
        # Clean up temp file
        os.unlink(temp_filename)
        
        # Print the transcription with wake word highlighted in red if present
        if wake_word in transcription:
            # Replace wake word with red-colored version
            colored_transcription = transcription.replace(wake_word, f"\033[91m{wake_word}\033[0m")
            print(f"Heard: '{colored_transcription}'")
        else:
            print(f"Heard: '{transcription}'")
        
        # Check if wake word is in transcription (with some flexibility)
        if wake_word in transcription or any(word.startswith(wake_word[:-1]) for word in transcription.split()):
            print(f"Wake word detected: '{transcription}'")
            return True

def record_user_prompt():
    """Record user's prompt using whisper-small model until silence is detected"""
    print("Listening for your prompt...")
    
    # Load the small model for detailed transcription
    model_small = whisper.load_model("small")
    
    # Audio parameters
    RATE = 16000
    CHANNELS = 1
    CHUNK_DURATION = 0.5  # Record in 0.5 second chunks
    SILENCE_THRESHOLD = 0.01  # Adjust based on your microphone and environment
    SILENCE_DURATION = 5  # 5 seconds of silence to end recording
    
    frames = []
    silent_chunks = 0
    silent_chunks_threshold = int(SILENCE_DURATION / CHUNK_DURATION)
    
    print("Speak your prompt now...")
    
    # Record until silence is detected
    while True:
        # Record audio for CHUNK_DURATION seconds
        chunk = sd.rec(int(CHUNK_DURATION * RATE), samplerate=RATE, channels=CHANNELS, dtype='float32')
        sd.wait()  # Wait until recording is finished
        
        frames.append(chunk)
        
        # Check for silence - calculate RMS of the audio chunk
        rms = np.sqrt(np.mean(chunk**2))
        if rms < SILENCE_THRESHOLD:
            silent_chunks += 1
            print(f"Silence detected ({silent_chunks}/{silent_chunks_threshold})...")
        else:
            silent_chunks = 0
        
        # If SILENCE_DURATION seconds of silence, stop recording
        if silent_chunks >= silent_chunks_threshold:
            break
    
    print("Finished recording, transcribing...")
    
    # Combine all audio chunks
    audio_data = np.vstack(frames)
    
    # Save to temporary WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
        temp_filename = temp_wav.name
    
    sf.write(temp_filename, audio_data, RATE, 'PCM_16')
    
    # Transcribe with whisper small
    result = model_small.transcribe(temp_filename)
    transcription = result["text"].strip()
    
    # Clean up temp file
    os.unlink(temp_filename)
    
    print(f"Transcribed prompt: '{transcription}'")
    return transcription

def GenerateOpenrouter(prompt):
    # You'll need to get an API key from https://openrouter.ai/
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        raise ValueError("Please set the OPENROUTER_API_KEY environment variable")
    
    # OpenRouter API endpoint
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Request headers
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-site.com", # Replace with your site
        "X-Title": "Poem Generator"
    }
    
    # Request body
    data = {
        "model": "qwen/qwq-32b:free",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    # Make the request
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        result = response.json()
        poem = result["choices"][0]["message"]["content"]
        print("Generated poem:")
        print(poem)
        return poem
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def text_to_speech(text):
    try:
        # Create a gTTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_filename = fp.name
            
        # Save the speech to the temporary file
        tts.save(temp_filename)
        
        # Play the audio file using the appropriate command based on OS
        system = platform.system()
        try:
            if system == 'Darwin':  # macOS
                subprocess.run(['afplay', temp_filename], check=True)
            elif system == 'Windows':
                os.startfile(temp_filename)
            else:  # Linux and other OS
                subprocess.run(['mpg123', temp_filename], check=True)
        except Exception as e:
            print(f"Could not play audio: {e}")
            print("You may need to install an audio player:")
            print("- On Linux: sudo apt-get install mpg123")
            print("- On macOS: afplay is built-in")
            print("- On Windows: Default media player is used")
            
        # Clean up the temporary file after playing
        try:
            os.unlink(temp_filename)
        except:
            pass
            
    except Exception as e:
        print(f"Text-to-speech error: {e}")
        print("\nHere's the poem text:")
        print(text)

def main():
    print("Starting Bonz - your voice-activated poem generator")
    print("Say 'bonz' to activate")
    
    while True:
        # Listen for wake word
        if listen_for_wake_word(wake_word="bonz"):
            # Record and transcribe user prompt
            user_prompt = record_user_prompt()
            
            # Generate poem
            poem = GenerateOpenrouter(user_prompt)
            
            if poem:
                # Convert to speech
                text_to_speech(poem)
        
        # Small delay before listening again
        time.sleep(0.5)

if __name__ == "__main__":
    main()