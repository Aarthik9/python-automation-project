from PIL import Image, ImageDraw, ImageFont
import json

def generate_slides(json_data):
    slides = json_data['presentation']['slides']
    theme = json_data['presentation']['theme']
    
    for slide in slides:
        img = Image.new('RGB', (800, 600), color='white')
        d = ImageDraw.Draw(img)
        
        # Title
        d.text((50, 50), slide.get('title', ''), fill=f"#{theme['primary_color']}", size=40)
        
        # Bullets
        y_offset = 150
        for block in slide.get('blocks', []):
            if block['type'] == 'bullets':
                for item in block['items']:
                    d.text((70, y_offset), f"• {item['text']}", fill="black")
                    y_offset += 40
                    
        img.save(f"output_images/Slide{slide['slide_index']}.png")

# Usage
with open('input.json') as f:
    data = json.load(f)
    generate_slides(data)