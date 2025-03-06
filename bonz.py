import os
import requests
import json
import time
from gtts import gTTS
import tempfile
import platform
import subprocess

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
    # Generate poem
    while True:
        poem = GenerateOpenrouter(input("Enter a prompt: "))
        
        if poem:
            # Convert to speech
            text_to_speech(poem)

if __name__ == "__main__":
    main()