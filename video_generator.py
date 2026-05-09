import json
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, AudioClip

# --- CONFIGURATION ---
IMG_DIR = "output_images"
AUD_DIR = "output_audio"
OUTPUT = "final_presentation_video.mp4"

def bake_subtitles(base_img_path, text):
    """
    Draws subtitles onto the image using Pillow.
    Bypasses ImageMagick to avoid font/binary errors.
    """
    img = Image.open(base_img_path).convert("RGB")
    width, height = img.size
    draw = ImageDraw.Draw(img)
    
    if text:
        # 1. Draw dark overlay bar at bottom
        bar_h = int(height * 0.18)
        draw.rectangle([0, height - bar_h, width, height], fill=(0, 0, 0, 170))
        
        # 2. Load Font (Standard Mac path)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except:
            font = ImageFont.load_default()
            
        # 3. Simple text wrapping
        max_w = width - 80
        words = text.split(' ')
        lines = []
        curr_line = []
        
        for word in words:
            curr_line.append(word)
            test_str = ' '.join(curr_line)
            bbox = draw.textbbox((0, 0), test_str, font=font)
            if (bbox[2] - bbox[0]) > max_w:
                curr_line.pop()
                lines.append(' '.join(curr_line))
                curr_line = [word]
        lines.append(' '.join(curr_line))

        # 4. Render wrapped text
        y_off = height - bar_h + 20
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            draw.text(((width - line_w) / 2, y_off), line, font=font, fill="white")
            y_off += (bbox[3] - bbox[1]) + 8
    
    return np.array(img)

def generate_video():
    if not os.path.exists('input.json'):
        print("❌ Error: input.json not found")
        return

    with open('input.json', 'r') as f:
        data = json.load(f)
    
    slides = data['presentation']['slides']
    clips = []

    print(f"🎬 Starting video assembly for {len(slides)} slides...")

    for slide in slides:
        idx = int(slide['slide_index'])
        img_path = os.path.join(IMG_DIR, f"Slide{idx}.png")
        aud_path = os.path.join(AUD_DIR, f"slide_{idx}.wav")

        if not os.path.exists(img_path):
            print(f"⚠️ Missing Slide{idx}.png, skipping.")
            continue

        # Extract subtitles from JSON
        subtitle_text = ""
        for block in slide.get('blocks', []):
            if block['type'] == 'bullets':
                subtitle_text = " • ".join([item['text'] for item in block['items']])
            elif block['type'] == 'text':
                subtitle_text = block['content']

        try:
            # --- AUDIO ---
            if os.path.exists(aud_path):
                audio = AudioFileClip(aud_path)
                dur = audio.duration
            else:
                dur = 3
                audio = AudioClip(lambda t: [0, 0], duration=dur).set_fps(44100)

            # --- FRAME PROCESSING ---
            # Bake text into the image using Pillow
            frame_np = bake_subtitles(img_path, subtitle_text)
            img_clip = ImageClip(frame_np).set_duration(dur)
            
            # Ken Burns zoom + Fades
            img_clip = img_clip.resize(lambda t: 1 + 0.03 * t).fadein(0.5).fadeout(0.5)
            
            # Combine
            clips.append(img_clip.set_audio(audio))
            print(f"✅ Slide {idx} processed.")

        except Exception as e:
            print(f"❌ Error on Slide {idx}: {e}")

    # --- FINAL RENDER ---
    if clips:
        print("🚀 Exporting final video...")
        final = concatenate_videoclips(clips, method="compose")
        # Fixed: Includes temp_audiofile to fix Mac sound issues
        final.write_videofile(
            OUTPUT, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            audio_bitrate="192k",
            temp_audiofile='temp-audio.m4a', 
            remove_temp=True
        )
        print(f"🔥 SUCCESS! Saved as: {OUTPUT}")
    else:
        print("❌ No clips were generated.")

if __name__ == "__main__":
    generate_video()