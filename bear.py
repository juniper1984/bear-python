import io
import os
import base64
import requests
import RPi.GPIO as GPIO
import keyboard
from picamera2 import Picamera2
import time
import pygame
import sys
import select
from dotenv import load_dotenv

load_dotenv()


# Initialize the camera
picam2 = Picamera2()
picam2.start()

# Define GPIO pin for the button
BUTTON_PIN = 17

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize pygame mixer
pygame.mixer.init()

# OpenAI API Key

api_key2 = os.getenv('OPEN_AI_KEY2')

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to generate speech from text using OpenAI API
def generate_speech(text, voice='nova', response_format='mp3', speed=1.0):
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key2}"
    }
    data = {
        "model": "tts-1",
        "input": text,
        "voice": voice,
        "response_format": response_format,
        "speed": speed
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to generate speech. Status code: {response.status_code}, Response: {response.text}")
        return None

def capture_and_process_image():
    image_path = "captured_image.jpg"
    picam2.capture_file(image_path)
    
    # Encode the captured image
    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key2}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What’s in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # Check the response status and print the description
    if response.status_code == 200:
        description = response.json().get('choices', [])[0].get('message', {}).get('content', 'No description found.')
        print(f"Image Description: {description}")
        # Generate speech from the description
        audio_content = generate_speech(description)
        if audio_content:
            # Save and play the audio
            audio_path = "description.mp3"
            with open(audio_path, "wb") as audio_file:
                audio_file.write(audio_content)
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(1)
    else:
        print(f"Failed to get description. Status code: {response.status_code}, Response: {response.text}")

print("Press the button to capture an image")

try:
    while True:
        button_state = GPIO.input(BUTTON_PIN)
        if button_state == GPIO.LOW:  # Button is pressed
            print("Button pressed, capturing image...")
            capture_and_process_image()
            time.sleep(1)  # Debounce delay
    
        if select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1)
            if key == ' ':
                print("Space bar pressed, capturing image...")
                capture_and_process_image()
                time.sleep(1)  # Debounce delay
finally:
    GPIO.cleanup()
    picam2.stop()

