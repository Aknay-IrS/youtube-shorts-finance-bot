"""
script_generator.py
Uses Claude API (haiku — cheapest) to write a punchy 55-second
finance Short script optimised for Indian audience.
Cost: ~₹0.08–0.15 per script.
"""

import json
import logging
import re

import anthropic

import config

log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)

SYSTEM_PROMPT = """You are a viral YouTube Shorts scriptwriter specialising in 
funny and mind-blowing animal facts for a global audience.

Your scripts:
- Start with a SHOCKING hook about the animal in first 3 seconds ("Wait... did you know...")
- Share 3-4 genuinely wild, surprising facts that sound unbelievable but are true
- Use a fun, energetic tone — like you can't believe this yourself
- Add funny commentary and reactions ("I'm not making this up!", "Scientists are confused too!")
- End with a CTA ("Follow for more insane animal facts!")
- Are 55 seconds when read at normal pace (~130 words)
- Feel entertaining and fun, like you're texting a friend the craziest thing you just learned

Keep sentences SHORT. Energy should be MAXIMUM. Facts must be 100% real and accurate."""


def generate_script(topic: str) -> dict:
    """
    Generate a complete Short script for the given topic.

    Returns dict with:
        - hook       : first 1-2 lines (stops the scroll)
        - body       : main content (2-3 tips)
        - cta        : call to action line
        - full_text  : complete script for TTS
        - title      : YouTube title (SEO optimised)
        - description: YouTube description
        - tags       : list of hashtags/keywords
    """
    prompt = f"""Write a funny animal facts YouTube Shorts script about: "{topic}"

Return ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "hook": "First 2-3 sentences that grab attention instantly",
  "body": "Main content with 2-3 concrete tips. Include specific numbers.",
  "cta": "Short closing line + follow CTA",
  "full_text": "Complete script hook + body + cta as one flowing text for voiceover",
  "title": "Clickable YouTube title under 60 chars with emoji",
  "description": "3-4 line YouTube description with keywords",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "pexels_search": "2-3 word search query for background video (e.g. money rupee india)"
}}

The full_text should be ~130 words, energetic spoken English, fun and surprising."""

    log.info(f"Generating script for: {topic}")

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        script = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f"JSON parse failed: {e}\nRaw: {raw[:300]}")
        # Fallback script
        script = _fallback_script(topic)

    # Append standard tags
    script["tags"] = list(set(
        script.get("tags", []) +
        ["Shorts", "AnimalFacts", "FunnyFacts", "Animals",
         "FunFacts", "WildFacts", "NatureShorts", "MindBlowing"]
    ))

    log.info(f"Script generated — title: {script.get('title', 'N/A')}")
    return script


def _fallback_script(topic: str) -> dict:
    """Returns a safe fallback if Claude's JSON is malformed."""
    clean = topic.replace('"', '')
    return {
        "hook": f"Suno! {clean} — yeh jaanna bahut zaroori hai!",
        "body": (
            "First, start small. Even ₹500 per month invested consistently "
            "can grow to lakhs over time thanks to compounding. "
            "Second, track every rupee you spend — most people waste ₹3000+ "
            "monthly without realising it. "
            "Third, automate your savings on salary day before you spend."
        ),
        "cta": "Follow for daily money tips that actually work!",
        "full_text": f"Suno! {clean} is something every Indian should know. "
                     "Start small with ₹500/month in SIP. Track your spending — "
                     "you're leaking ₹3000+ monthly. Automate savings on salary day. "
                     "These three habits can change your financial life. "
                     "Follow for daily money tips that actually work!",
        "title": f"💰 {clean[:45]} #Shorts",
        "description": f"Learn about {clean} and how to improve your finances in India.\n"
                        "#PersonalFinance #MoneyTips #India #Shorts",
        "tags": ["MoneyTips", "PersonalFinance", "India", "Shorts"],
        "pexels_search": "money india rupee",
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = generate_script("how to save money on ₹25,000 salary in India")
    print(json.dumps(s, indent=2, ensure_ascii=False))
