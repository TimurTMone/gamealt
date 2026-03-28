#!/usr/bin/env python3
"""
🖍️ Coloring Page Agent
========================
Generates printable coloring pages using Leonardo.ai API.
Outputs high-contrast line art suitable for toddlers/kids.

Usage:
    python3 coloring_agent.py                    # Generate default animal pack
    python3 coloring_agent.py --theme animals    # Specific theme
    python3 coloring_agent.py --theme alphabet   # A-Z coloring pages
    python3 coloring_agent.py --count 10         # Generate 10 pages
"""

import argparse
import json
import os
import time
import requests
from datetime import datetime

from config import (
    LEONARDO_API_KEY, COLORING_DIR,
    LEONARDO_MODEL_ID, LEONARDO_COLORING_STYLE
)

LEONARDO_API_BASE = "https://cloud.leonardo.ai/api/rest/v1"

# ── THEME DEFINITIONS ──
THEMES = {
    "animals": {
        "name": "Animals",
        "subjects": [
            "a cute cat sitting", "a friendly dog with a ball", "a happy cow in a field",
            "a smiling horse running", "a little bird on a branch", "a goldfish in a bowl",
            "a fluffy sheep", "a baby chicken hatching", "a cuddly bear",
            "a bunny rabbit with long ears", "a playful dolphin jumping",
            "a gentle elephant", "a tall giraffe", "a happy penguin",
            "a sleeping owl on a branch", "a colorful butterfly",
            "a snail with a spiral shell", "a baby turtle", "a ladybug on a leaf",
            "a frog sitting on a lily pad"
        ]
    },
    "alphabet": {
        "name": "Alphabet",
        "subjects": [f"the letter {chr(65+i)} with a cute {obj}" for i, obj in enumerate([
            "apple", "bear", "cat", "dog", "elephant", "fish", "giraffe", "house",
            "ice cream", "jellyfish", "kite", "lion", "moon", "nest", "octopus",
            "penguin", "queen", "rabbit", "sun", "tree", "umbrella", "violin",
            "whale", "xylophone", "yacht", "zebra"
        ])]
    },
    "numbers": {
        "name": "Numbers 1-10",
        "subjects": [
            "the number 1 with one star", "the number 2 with two hearts",
            "the number 3 with three balloons", "the number 4 with four flowers",
            "the number 5 with five butterflies", "the number 6 with six fish",
            "the number 7 with seven birds", "the number 8 with eight circles",
            "the number 9 with nine apples", "the number 10 with ten dots"
        ]
    },
    "family": {
        "name": "Family & Daily Life",
        "subjects": [
            "a family eating together at a table", "a parent reading a book to a child",
            "a child brushing teeth", "a child playing with blocks",
            "a parent and child at the park", "a child sleeping in bed with a teddy bear",
            "a child taking a bath with rubber ducks", "a family walking together",
            "a child drawing with crayons", "a parent pushing a child on a swing"
        ]
    },
    "vehicles": {
        "name": "Vehicles",
        "subjects": [
            "a simple car", "a big truck", "a fire engine", "an airplane in the sky",
            "a boat on water", "a train on tracks", "a bicycle", "a rocket ship",
            "a hot air balloon", "a helicopter"
        ]
    }
}

COLORING_PROMPT_TEMPLATE = (
    "Simple black and white line art coloring page for toddlers, {subject}, "
    "thick clean outlines, no shading, no gray areas, no background details, "
    "minimal detail, very simple shapes, large areas to color, "
    "white background, children's coloring book style, "
    "age appropriate for 2-4 year olds"
)

NEGATIVE_PROMPT = (
    "color, shading, gradient, gray, realistic, detailed, complex, "
    "thin lines, small details, scary, dark, photograph, 3d render"
)


def generate_image_leonardo(prompt: str, negative_prompt: str = "") -> dict:
    """Submit a generation request to Leonardo.ai API."""
    if not LEONARDO_API_KEY:
        return {"error": "LEONARDO_API_KEY not set. Set it in config.py or env var."}

    headers = {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt or NEGATIVE_PROMPT,
        "modelId": LEONARDO_MODEL_ID,
        "width": LEONARDO_COLORING_STYLE["width"],
        "height": LEONARDO_COLORING_STYLE["height"],
        "num_images": LEONARDO_COLORING_STYLE["num_images"],
        "guidance_scale": LEONARDO_COLORING_STYLE["guidance_scale"],
    }

    # Submit generation
    resp = requests.post(
        f"{LEONARDO_API_BASE}/generations",
        headers=headers,
        json=payload
    )

    if resp.status_code != 200:
        return {"error": f"API error {resp.status_code}: {resp.text}"}

    gen_id = resp.json().get("sdGenerationJob", {}).get("generationId")
    if not gen_id:
        return {"error": f"No generation ID returned: {resp.text}"}

    # Poll for completion
    for attempt in range(30):
        time.sleep(4)
        poll = requests.get(
            f"{LEONARDO_API_BASE}/generations/{gen_id}",
            headers=headers
        )
        if poll.status_code == 200:
            data = poll.json().get("generations_by_pk", {})
            status = data.get("status")
            if status == "COMPLETE":
                images = data.get("generated_images", [])
                return {"success": True, "images": images, "gen_id": gen_id}
            elif status == "FAILED":
                return {"error": "Generation failed"}

    return {"error": "Timed out waiting for generation"}


def download_image(url: str, filepath: str) -> bool:
    """Download an image from URL to local file."""
    try:
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return False


def generate_coloring_pack(theme: str = "animals", count: int = None) -> dict:
    """Generate a full coloring page pack for a theme."""
    if theme not in THEMES:
        return {"error": f"Unknown theme '{theme}'. Available: {list(THEMES.keys())}"}

    theme_data = THEMES[theme]
    subjects = theme_data["subjects"]
    if count:
        subjects = subjects[:count]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pack_dir = os.path.join(COLORING_DIR, f"{theme}_{timestamp}")
    os.makedirs(pack_dir, exist_ok=True)

    report = {
        "theme": theme,
        "name": theme_data["name"],
        "timestamp": timestamp,
        "total": len(subjects),
        "success": 0,
        "failed": 0,
        "pages": [],
        "output_dir": pack_dir
    }

    print(f"\n🖍️  COLORING AGENT — Generating '{theme_data['name']}' pack")
    print(f"   Pages: {len(subjects)} | Output: {pack_dir}\n")

    for i, subject in enumerate(subjects):
        prompt = COLORING_PROMPT_TEMPLATE.format(subject=subject)
        filename = f"page_{i+1:02d}_{subject.replace(' ', '_')[:30]}.png"
        filepath = os.path.join(pack_dir, filename)

        print(f"  [{i+1}/{len(subjects)}] Generating: {subject}...")

        result = generate_image_leonardo(prompt)

        if result.get("success") and result.get("images"):
            img_url = result["images"][0].get("url")
            if img_url and download_image(img_url, filepath):
                print(f"  ✓ Saved: {filename}")
                report["success"] += 1
                report["pages"].append({"file": filename, "subject": subject, "status": "ok"})
            else:
                report["failed"] += 1
                report["pages"].append({"file": filename, "subject": subject, "status": "download_failed"})
        elif result.get("error"):
            print(f"  ✗ Error: {result['error']}")
            report["failed"] += 1
            report["pages"].append({"file": filename, "subject": subject, "status": result["error"]})

    # Save report
    report_path = os.path.join(pack_dir, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*50}")
    print(f"  ✓ Done! {report['success']}/{report['total']} pages generated")
    print(f"  📁 Output: {pack_dir}")
    print(f"  📋 Report: {report_path}")

    return report


def list_themes():
    """Print available themes."""
    print("\n🖍️  Available Coloring Themes:\n")
    for key, theme in THEMES.items():
        print(f"  {key:12s} — {theme['name']} ({len(theme['subjects'])} pages)")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BabyPath Coloring Page Agent")
    parser.add_argument("--theme", default="animals", help="Theme to generate")
    parser.add_argument("--count", type=int, help="Number of pages (default: all)")
    parser.add_argument("--list", action="store_true", help="List available themes")
    args = parser.parse_args()

    if args.list:
        list_themes()
    else:
        if not LEONARDO_API_KEY:
            print("\n⚠️  LEONARDO_API_KEY not set!")
            print("   Set it: export LEONARDO_API_KEY='your-key-here'")
            print("   Get it: https://cloud.leonardo.ai → API → Generate API Key\n")
            list_themes()
        else:
            generate_coloring_pack(args.theme, args.count)
