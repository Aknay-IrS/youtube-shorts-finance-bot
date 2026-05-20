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
personal finance content for Indian audiences aged 18-35. 

Your scripts:
- Start with a HOOK that makes people stop scrolling in the first 3 seconds
- Use simple Hindi-English (Hinglish) words naturally (bhai, yaar, dekho, suno)
- Give 2-3 concrete, actionable tips — specific numbers and steps
- End with a strong CTA ("Follow for daily money tips!")
- Are 55 seconds when read at normal pace (~130 words)
- Feel like a knowledgeable friend talking, not a formal lecture
- Include a relatable pain point Indians face (low salary, inflation, EMIs)

Never use complex financial jargon. Keep sentences short. Energy should be HIGH."""


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
    prompt = f"""Write a YouTube Shorts script about: "{topic}"

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

The full_text should be ~130 words, natural spoken English with some Hinglish."""

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
        ["Shorts", "MoneyTips", "PersonalFinance", "IndiaFinance",
         "MoneyInIndia", "FinanceTips", "SaveMoney"]
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
