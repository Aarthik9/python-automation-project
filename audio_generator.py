import pyttsx3
import json
import os
import time

# Initialize engine
engine = pyttsx3.init()
engine.setProperty('rate', 150) # Slightly faster for better natural flow

# Ensure output directory exists
os.makedirs("output_audio", exist_ok=True)

with open("input.json") as f:
    data = json.load(f)

slides = data["presentation"]["slides"]

for i, slide in enumerate(slides, 1):
    # Construct narration text
    text = f"{slide.get('title', '')}. {slide.get('subtitle', '')}. "
    
    for block in slide.get("blocks", []):
        if block["type"] == "bullets":
            for item in block["items"]:
                text += f"{item['text']}. "
        elif block["type"] == "text":
            text += f"{block['content']}. "

    file_path = os.path.abspath(f"output_audio/slide_{i}.wav")
    
    # Save to file
    engine.save_to_file(text, file_path)
    print(f"🔊 Queuing audio for Slide {i}")

# CRITICAL: This executes the saving process
engine.runAndWait()

# Small delay to ensure OS handles file closure
time.sleep(2) 
print("✅ All audio generated and saved to disk.")