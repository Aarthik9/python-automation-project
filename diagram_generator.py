import os
import json
import matplotlib.pyplot as plt
from matplotlib_venn import venn2

# create folder if not exists
os.makedirs("output_images", exist_ok=True)

# load your SAME input.json
with open("input.json") as f:
    data = json.load(f)

slides = data.get("presentation", {}).get("slides", [])

count = 1

for slide in slides:

    # ---------- VENN ----------
    if slide.get("type") == "venn":

        labels = slide.get("labels", ["A", "B"])
        values = slide.get("values", [10, 10, 5])
        title = slide.get("title", "")

        plt.figure(figsize=(5,5))
        venn2(subsets=values, set_labels=labels)
        plt.title(title)

        path = f"output_images/slide_{count}.png"
        plt.savefig(path)
        plt.close()

        print(f"✅ Venn created: {path}")
        count += 1


    # ---------- CHART ----------
    if slide.get("type") == "chart":

        labels = slide.get("labels", [])
        values = slide.get("values", [])
        title = slide.get("title", "")

        plt.figure(figsize=(6,4))
        plt.bar(labels, values)
        plt.title(title)

        path = f"output_images/chart_{count}.png"
        plt.savefig(path)
        plt.close()

        print(f"📊 Chart created: {path}")
        count += 1