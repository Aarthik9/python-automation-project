import json
import matplotlib.pyplot as plt
from matplotlib_venn import venn2

def generate_venn():
    with open('input.json', 'r') as f:
        data = json.load(f)

    for slide in data['presentation']['slides']:
        if slide.get('type') == 'venn':
            plt.figure(figsize=(8, 6))
            venn2(subsets=tuple(slide['values']), set_labels=tuple(slide['labels']))
            plt.title(slide['title'])
            # Save as Slide3.png to match video generator expectation
            plt.savefig(f"output_images/Slide{int(slide['slide_index'])}.png")
            plt.close()
            print("✅ Venn Diagram Generated as Slide3.png")

if __name__ == "__main__":
    generate_venn()