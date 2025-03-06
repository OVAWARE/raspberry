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
import whisper
import pyaudio
import wave
import audioop

def listen_for_wake_word(wake_word="bonz", timeout=None):
    """Listen for the wake word using whisper-tiny model"""
    print(f"Listening for wake word: '{wake_word}'...")
    
    # Load the tiny model for wake word detection
    model_tiny = whisper.load_model("tiny")
    
    # Audio parameters
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    start_time = time.time()
    frames = []
    
    # Listen for 2 seconds at a time to check for wake word
    while True:
        if timeout and (time.time() - start_time) > timeout:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            return False
        
        # Collect 2 seconds of audio
        frames = []
        for _ in range(0, int(RATE / CHUNK * 2)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
            temp_filename = temp_wav.name
        
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Transcribe with whisper tiny
        result = model_tiny.transcribe(temp_filename)
        transcription = result["text"].lower().strip()
        
        # Clean up temp file
        os.unlink(temp_filename)
        
        # Check if wake word is in transcription (with some flexibility)
        if wake_word in transcription or any(word.startswith(wake_word[:-1]) for word in transcription.split()):
            print(f"Wake word detected: '{transcription}'")
            stream.stop_stream()
            stream.close()
            audio.terminate()
            return True
        
        print("Listening...")

def record_user_prompt():
    """Record user's prompt using whisper-small model until silence is detected"""
    print("Listening for your prompt...")
    
    # Load the small model for detailed transcription
    model_small = whisper.load_model("small")
    
    # Audio parameters
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    SILENCE_THRESHOLD = 500  # Adjust based on your microphone and environment
    SILENCE_DURATION = 5  # 5 seconds of silence to end recording
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    frames = []
    silent_chunks = 0
    silent_chunks_threshold = int(SILENCE_DURATION * RATE / CHUNK)
    
    print("Speak your prompt now...")
    
    # Record until silence is detected
    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        
        # Check for silence
        rms = audioop.rms(data, 2)
        if rms < SILENCE_THRESHOLD:
            silent_chunks += 1
        else:
            silent_chunks = 0
        
        # If 5 seconds of silence, stop recording
        if silent_chunks >= silent_chunks_threshold:
            break
    
    print("Finished recording, transcribing...")
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # Save to temporary WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
        temp_filename = temp_wav.name
    
    wf = wave.open(temp_filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
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