#!/usr/bin/env python3
"""
📖 Guide & eBook Agent
========================
Generates parent guides and eBooks using Claude API.
Outputs structured HTML files ready for PDF conversion.

Usage:
    python3 guide_agent.py                          # Generate all guides
    python3 guide_agent.py --guide speech-delay      # Specific guide
    python3 guide_agent.py --guide first-words --lang ru  # Russian version
    python3 guide_agent.py --list                    # List available guides
"""

import argparse
import json
import os
from datetime import datetime

import anthropic

from config import ANTHROPIC_API_KEY, GUIDES_DIR, CLAUDE_MODEL, LANGUAGES

# ── GUIDE DEFINITIONS ──
GUIDES = {
    "first-words": {
        "title": {
            "en": "The First 50 Words: A Parent's Complete Checklist",
            "ru": "Первые 50 слов: Полный чек-лист для родителей",
            "ky": "Биринчи 50 сөз: Ата-энелер үчүн толук тизме"
        },
        "description": "Tracks the first 50 words every toddler should learn, organized by category with practice tips.",
        "prompt": """Create a comprehensive, warm, and practical parent guide called "The First 50 Words."

Structure:
1. **Introduction** (1 page): Why first words matter, what counts as a "word" (approximations count!), and how to use this guide.
2. **How Children Learn Words** (1 page): Brief, evidence-based explanation. Reference Hanen "It Takes Two to Talk" approach. Key principles: model don't demand, accept approximations, repetition is key.
3. **The 50 Words Checklist** organized by category:
   - Social words (hi, bye, please, thank you, yes, no, uh-oh) — 7 words
   - People (mama, papa, baby, grandma, grandpa) — 5 words
   - Food & drink (milk, water, juice, bread, banana, apple, cookie, more) — 8 words
   - Animals (dog, cat, bird, fish, cow, horse) — 6 words
   - Actions (eat, drink, sleep, go, stop, open, help, play, wash, read) — 10 words
   - Body parts (eye, nose, mouth, ear, hand, foot, head) — 7 words
   - Descriptors & concepts (big, little, hot, cold, more, all done, up) — 7 words

   For EACH word include:
   - The word in {lang_name}
   - A checkbox □
   - Target sound (e.g., /m/ for mama)
   - One practical tip for parents (2 sentences max)
   - What approximation to accept (e.g., "ba" for ball)

4. **Tracking Sheet** (1 page): A simple table with Date | New Word | Context | Notes columns.
5. **When to Seek Help** (half page): Red flags from ASHA guidelines. Encouraging but honest.
6. **Daily Routine Cheat Sheet** (1 page): 5 daily moments (mealtime, bath, play, outside, bedtime) with 3 words to target in each.

Tone: Warm, encouraging, NO guilt-tripping. Written for BOTH parents (not just moms). Short sentences, practical focus. Use simple {lang_name} throughout.

Format: Output as clean HTML with inline CSS suitable for printing as A4 PDF. Use a warm, readable font. Include page breaks between sections."""
    },

    "speech-delay": {
        "title": {
            "en": "When Your Child Isn't Talking Yet: A Parent's Survival Guide",
            "ru": "Когда ваш ребёнок ещё не говорит: Руководство для родителей",
            "ky": "Балаңыз али сүйлөбөй жатканда: Ата-энелер үчүн колдонмо"
        },
        "description": "30-page guide for parents of late talkers. Evidence-based, compassionate, practical.",
        "prompt": """Create a comprehensive guide for parents whose toddler has a speech delay.

Structure:
1. **You're Not Alone** (intro): Normalize the experience. Statistics on late talkers (15-20% of 2-year-olds). This is common. Written in {lang_name}.
2. **What's Normal? Speech Milestones**: Clear, age-by-age milestones from 6 months to 3 years. Based on ASHA guidelines.
3. **Late Talker vs. Something More**: How to tell the difference. Risk factors. What professionals look for.
4. **10 Things You Can Do TODAY**: Practical, evidence-based strategies parents can implement immediately:
   - OWL: Observe, Wait, Listen (Hanen approach)
   - Model, don't demand ("Say ball!" doesn't work)
   - Follow their lead
   - Use routines as language opportunities
   - Narrate your day (parallel talk, self-talk)
   - Read together (interactive reading, not passive)
   - Reduce screen time, increase interaction time
   - Accept approximations as real words
   - Use gestures alongside words
   - Celebrate every attempt

   For each strategy: 2-3 concrete examples of how to apply it.

5. **The Bilingual Question**: Evidence that bilingualism does NOT cause delays. How to count vocabulary across languages. Keep using all home languages.
6. **Getting Professional Help**: What is an SLP? How to find one. What to expect in an evaluation. How to advocate for your child. Early intervention programs.
7. **For Dads Specifically**: Why paternal involvement matters for speech. How dads can uniquely contribute. Addressing the "mom knows best" myth.
8. **Self-Care for Parents**: The emotional toll of worrying about your child's development. It's okay to feel frustrated. Community resources.
9. **Quick Reference Card**: One-page summary of key strategies and red flags.

Tone: Compassionate, evidence-based, empowering. NO blame. NO judgment. Written for BOTH parents equally in {lang_name}.

Format: Clean HTML with inline CSS for A4 PDF printing. Warm design, readable fonts, clear headings."""
    },

    "bilingual-handbook": {
        "title": {
            "en": "Raising a Bilingual Child: The Practical Handbook",
            "ru": "Воспитание двуязычного ребёнка: Практическое руководство",
            "ky": "Эки тилдүү баланы тарбиялоо: Практикалык колдонмо"
        },
        "description": "How to raise a bilingual/trilingual child. Strategies, word lists, daily plans.",
        "prompt": """Create a practical handbook for raising bilingual or trilingual children, focused on English, Russian, and Kyrgyz.

Structure:
1. **Bilingualism Is a Gift**: Introduction. Research shows bilingualism strengthens cognitive development, NOT delays it. (Petitto et al., 2001; Bialystok, 2001).
2. **Common Strategies**:
   - OPOL (One Parent, One Language): How it works, pros/cons
   - Time & Place: Language by location/time
   - Minority Language at Home: Why this often works best
   - Mixed approach: What most families actually do
3. **Language Mixing Is Normal**: Code-switching is a SIGN of bilingual competence, not confusion.
4. **Vocabulary Across Languages**: How to properly count your child's words. A bilingual child's TOTAL vocabulary (all languages combined) is what matters.
5. **100 Essential Words in 3 Languages**: A reference table with English, Russian, and Kyrgyz columns:
   - 20 core/functional words
   - 20 people/family words
   - 20 food/drink words
   - 20 animal words
   - 20 action/descriptor words
6. **Daily Plan**: A sample daily schedule showing when to use which language naturally.
7. **For When Others Doubt You**: How to respond to "You'll confuse them!" and other myths.
8. **Resources**: Books, apps (including BabyPath!), communities.

Tone: Encouraging, practical, research-backed. Written in {lang_name}. Include occasional phrases in all three languages to model trilingual thinking.

Format: Clean HTML with inline CSS for A4 PDF. Tables for word lists. Include page breaks."""
    },

    "daily-routines": {
        "title": {
            "en": "Routine Cards: Turn Every Moment Into a Language Lesson",
            "ru": "Карточки рутин: Каждый момент — урок языка",
            "ky": "Күндөлүк карталар: Ар бир учурду тил сабагына айландыр"
        },
        "description": "Printable routine cards with target words for mealtime, bath, bedtime, play, outside.",
        "prompt": """Create a set of printable routine cards for parents to use during daily activities with their toddler.

For EACH of these 5 routines, create a card:
1. **Mealtime** 🍽️
2. **Bath Time** 🛁
3. **Playtime** 🎮
4. **Outside / Walk** ☀️
5. **Bedtime** 🌙

Each card should include (in {lang_name}):
- Routine name and emoji
- 8 target words for this routine (with the word in English, Russian, and Kyrgyz in a small table)
- 3 specific things to SAY during this routine (example phrases)
- 2 specific things to DO (actions/gestures)
- 1 "power tip" based on speech therapy research
- A small "What to accept" box showing what approximations are fine

Design: Each card should be printable on one A4 page. Colorful but not overwhelming. Large font for the target words. Parents can tape these in the kitchen, bathroom, bedroom.

Format: Clean HTML with inline CSS. Each card on its own page (page-break-after). Bright, cheerful design with rounded corners and soft colors."""
    }
}


def generate_guide(guide_id: str, lang: str = "en") -> dict:
    """Generate a guide using Claude API."""
    if guide_id not in GUIDES:
        return {"error": f"Unknown guide '{guide_id}'. Available: {list(GUIDES.keys())}"}

    if not ANTHROPIC_API_KEY:
        return {"error": "ANTHROPIC_API_KEY not set."}

    guide = GUIDES[guide_id]
    lang_name = LANGUAGES.get(lang, "English")
    title = guide["title"].get(lang, guide["title"]["en"])

    print(f"\n📖 GUIDE AGENT — Generating: {title}")
    print(f"   Language: {lang_name} | Guide: {guide_id}\n")

    prompt = guide["prompt"].replace("{lang_name}", lang_name)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": f"""You are an expert pediatric speech-language pathologist and parent educator.

{prompt}

IMPORTANT:
- Write everything in {lang_name}
- The title is: "{title}"
- This is for BabyPath (babypath.app) — a platform for parents of young children
- Add "Generated by BabyPath — babypath.app" in the footer of each page
- Output ONLY the HTML content, no markdown code fences"""
            }]
        )

        html_content = message.content[0].text

        # Clean up if wrapped in code fences
        if html_content.startswith("```"):
            html_content = html_content.split("\n", 1)[1]
        if html_content.endswith("```"):
            html_content = html_content.rsplit("```", 1)[0]

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{guide_id}_{lang}_{timestamp}.html"
        filepath = os.path.join(GUIDES_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        report = {
            "guide": guide_id,
            "title": title,
            "lang": lang,
            "file": filepath,
            "timestamp": timestamp,
            "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
            "status": "success"
        }

        print(f"  ✓ Generated: {filepath}")
        print(f"  📊 Tokens used: {report['tokens_used']}")

        # Save report
        report_path = filepath.replace(".html", "_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"error": str(e)}


def generate_all_guides(lang: str = "en") -> list:
    """Generate all guides in a specific language."""
    results = []
    for guide_id in GUIDES:
        result = generate_guide(guide_id, lang)
        results.append(result)
    return results


def list_guides():
    """Print available guides."""
    print("\n📖 Available Guides:\n")
    for key, guide in GUIDES.items():
        print(f"  {key:20s} — {guide['title']['en']}")
        print(f"  {'':20s}   {guide['description']}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BabyPath Guide Agent")
    parser.add_argument("--guide", help="Guide ID to generate (or 'all')")
    parser.add_argument("--lang", default="en", choices=["en", "ru", "ky"], help="Language")
    parser.add_argument("--list", action="store_true", help="List available guides")
    args = parser.parse_args()

    if args.list:
        list_guides()
    elif not ANTHROPIC_API_KEY:
        print("\n⚠️  ANTHROPIC_API_KEY not set!")
        print("   Set it: export ANTHROPIC_API_KEY='your-key-here'")
        print("   Get it: https://console.anthropic.com\n")
        list_guides()
    elif args.guide == "all":
        generate_all_guides(args.lang)
    elif args.guide:
        generate_guide(args.guide, args.lang)
    else:
        list_guides()
        print("  Usage: python3 guide_agent.py --guide speech-delay --lang en\n")
