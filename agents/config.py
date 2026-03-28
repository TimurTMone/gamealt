"""
BabyPath AI Agent Configuration
================================
Set your API keys here or via environment variables.
"""
import os

# === API KEYS (set via env vars or edit directly) ===
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
HIGGSFIELD_API_KEY = os.getenv("HIGGSFIELD_API_KEY", "")

# === OUTPUT DIRECTORIES ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "generated")
COLORING_DIR = os.path.join(OUTPUT_DIR, "coloring-pages")
GUIDES_DIR = os.path.join(OUTPUT_DIR, "guides")
BILINGUAL_DIR = os.path.join(OUTPUT_DIR, "bilingual-kits")
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")

# Create all dirs
for d in [COLORING_DIR, GUIDES_DIR, BILINGUAL_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

# === LANGUAGES ===
LANGUAGES = {
    "en": "English",
    "ru": "Russian",
    "ky": "Kyrgyz"
}

# === LEONARDO.AI SETTINGS ===
LEONARDO_MODEL_ID = "6b645e3a-d64f-4341-a6d8-7a3690fbf042"  # Leonardo Creative
LEONARDO_COLORING_STYLE = {
    "width": 1024,
    "height": 1024,
    "num_images": 1,
    "guidance_scale": 7,
}

# === CLAUDE SETTINGS ===
CLAUDE_MODEL = "claude-sonnet-4-20250514"
