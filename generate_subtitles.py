import os
import json
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips, AudioClip
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.editor import TextClip, CompositeVideoClip
from moviepy.config import change_settings

# --- MAC IMAGE MAGICK PATH ---
# Directing MoviePy to the Homebrew installation of Magick
change_settings({"IMAGEMAGICK_BINARY": "/opt/homebrew/bin/magick"})

IMG_DIR = "output_images"
AUD_DIR = "output_audio"
OUTPUT = "final_presentation_video.mp4"

def generate_video():
    # Load JSON to get slide count and metadata
    with open('input.json', 'r') as f:
        data = json.load(f)
    
    slides = data['presentation']['slides']
    clips = []

    # Subtitle Style: Bold Arial, white text with a black stroke for visibility
    def subtitle_generator(txt):
        return TextClip(
            txt, 
            font='Helvetica', 
            fontsize=32, 
            color='white', 
            stroke_color='black', 
            stroke_width=1,
            method='caption',
            size=(1100, None)
        )

    print(f"🎬 Compiling video from {len(slides)} slides...")

    for slide in slides:
        idx = int(slide['slide_index'])
        img_path = os.path.join(IMG_DIR, f"Slide{idx}.png")
        aud_path = os.path.join(AUD_DIR, f"slide_{idx}.wav")
        srt_path = os.path.join(AUD_DIR, f"slide_{idx}.srt")

        if not os.path.exists(img_path):
            print(f"⚠️ Missing Slide {idx}, skipping...")
            continue

        try:
            # 1. Handle Audio & Duration
            if os.path.exists(aud_path):
                audio = AudioFileClip(aud_path)
                duration = audio.duration
            else:
                duration = 3 
                audio = AudioClip(lambda t: [0, 0], duration=duration).set_fps(44100)

            # 2. Setup Image Clip with Ken Burns effect (Subtle Zoom)
            img_clip = ImageClip(img_path).set_duration(duration)
            img_clip = img_clip.resize(lambda t: 1 + 0.03 * t)

            # 3. Layer Subtitles (The Whisper .srt files)
            if os.path.exists(srt_path):
                subtitles = SubtitlesClip(srt_path, subtitle_generator).set_duration(duration)
                slide_clip = CompositeVideoClip([
                    img_clip, 
                    subtitles.set_position(('center', 600)) # Position near bottom
                ])
            else:
                slide_clip = img_clip

            # 4. Apply transitions and attach audio
            slide_clip = slide_clip.fadein(0.5).fadeout(0.5).set_audio(audio)
            clips.append(slide_clip)
            print(f"✅ Slide {idx} processed.")

        except Exception as e:
            print(f"❌ Error on Slide {idx}: {e}")

    # 5. Final Export
    if clips:
        print("🚀 Rendering final video... this might take a minute.")
        final_video = concatenate_videoclips(clips, method="compose")
        final_video.write_videofile(
            OUTPUT, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac"
        )
        print(f"🔥 SUCCESS! Final video: {OUTPUT}")
    else:
        print("❌ No clips were created. Check your folder paths.")

if __name__ == "__main__":
    generate_video()