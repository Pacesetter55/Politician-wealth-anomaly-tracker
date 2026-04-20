import os
from groq import Groq
from dotenv import load_dotenv
from analyzer import format_inr, detect_discrepancies, wealth_growth_pct

load_dotenv()

MODEL = "llama-3.1-8b-instant"
_client = Groq(api_key=os.environ["GROQ_API_KEY"])


def build_politician_context(profiles: list[dict]) -> str:
    """Build a rich text context about the politician from scraped profiles."""
    if not profiles:
        return "No data available."

    latest = max(profiles, key=lambda x: x.get("year", "0"))
    name = latest.get("name", "Unknown")
    lines = [
        f"POLITICIAN: {name}",
        f"Party: {latest.get('party', 'N/A')}",
        f"Constituency: {latest.get('constituency', 'N/A')} ({latest.get('state', 'N/A')})",
        f"Education: {latest.get('education', 'N/A')}",
        "",
        "=== ELECTION HISTORY (Lok Sabha) ===",
    ]

    for p in sorted(profiles, key=lambda x: x.get("year", "0")):
        lines.append(
            f"\nYear: {p.get('year', '?')} | "
            f"Party: {p.get('party', 'N/A')} | "
            f"Constituency: {p.get('constituency', 'N/A')}"
        )
        lines.append(
            f"  Total Assets: {format_inr(p.get('total_assets', 0))} | "
            f"Total Liabilities: {format_inr(p.get('total_liabilities', 0))}"
        )
        lines.append(
            f"  Movable Assets: {format_inr(p.get('movable_assets', 0))} | "
            f"Immovable Assets: {format_inr(p.get('immovable_assets', 0))}"
        )
        lines.append(
            f"  Criminal Cases Declared: {p.get('num_criminal_cases', 0)}"
        )
        if p.get("criminal_cases"):
            for c in p["criminal_cases"][:3]:
                lines.append(f"    - {c}")

    growth = wealth_growth_pct(profiles)
    if growth:
        lines.append("\n=== WEALTH GROWTH BETWEEN ELECTIONS ===")
        for g in growth:
            lines.append(
                f"  {g['from_year']} → {g['to_year']}: "
                f"{g['from_assets']} → {g['to_assets']} "
                f"({'+' if g['growth_pct'] > 0 else ''}{g['growth_pct']}%)"
            )

    flags = detect_discrepancies(profiles)
    if flags:
        lines.append("\n=== DISCREPANCIES / FLAGS ===")
        for f in flags:
            lines.append(f"  [{f['severity']}] {f['type']}: {f['detail']}")

    return "\n".join(lines)


def chat(
    user_message: str,
    profiles: list[dict],
    history: list[dict],
) -> str:
    context = build_politician_context(profiles)

    system_prompt = f"""You are a civic-intelligence assistant helping Indian citizens understand their political candidates for Lok Sabha elections.

You have access to the following data scraped from the official Election Commission affidavits via myneta.info:

{context}

Guidelines:
- Be factual and cite specific numbers from the data.
- Flag any concerning patterns (sudden wealth jumps, criminal cases) clearly.
- Be neutral and non-partisan — your job is to inform, not to judge.
- If asked something not in the data, say so clearly.
- Use Indian number system (Crore, Lakh) in your answers.
- Help citizens make informed decisions by explaining what the data means in simple language.
- When discussing criminal cases, note that "declared" ≠ "convicted" — presumption of innocence applies.
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_message})

    try:
        response = _client.chat.completions.create(model=MODEL, messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to Groq: {e}"


def get_quick_summary(profiles: list[dict]) -> str:
    """Generate an AI summary of the politician without user interaction."""
    if not profiles:
        return "No data found for this politician."

    context = build_politician_context(profiles)
    prompt = (
        "Based on the election affidavit data provided, write a concise 3-4 paragraph "
        "summary of this politician for an Indian voter. Cover: (1) who they are, "
        "(2) wealth trajectory and key figures, (3) criminal cases if any, "
        "(4) any notable discrepancies or flags. Be factual and balanced."
    )

    system = f"""You are a civic-intelligence assistant. Here is the politician data:

{context}

Guidelines: Be factual, use Indian number system, note criminal cases without assuming guilt, flag suspicious patterns."""

    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not generate AI summary: {e}"
