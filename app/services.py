"""
Service layer for AI and other backend-like operations.
Currently includes the investment thesis parsing helper.
"""

from typing import Optional, Any, Dict, List

from app.config import get_api_key


def parse_investment_thesis(thesis_text: str, client: Optional[Any]) -> Dict[str, Any]:
    """
    Parse a free-text investment thesis into a structured schema suitable for UI population.
    Returns a dict with keys:
      - sectors: List[str]
      - geography: List[str]
      - stages: List[str]   (selected stages)
      - ticket_min: int     (euros)
      - ticket_max: int     (euros)
      - scoring: Dict[str, int] with keys: team_quality, tech_readiness, market_size, geography_fit, traction, ticket_fit
      - flags: List[str]    (auto-flag rules)
      - rejects: List[str]  (auto-reject rules)
      - notes: str
    On failure, returns best-effort defaults possibly with notes set to an error message.
    """
    import json
    import re

    def defaults() -> Dict[str, Any]:
        # Base defaults used when UI first loads (not for parsed empties policy)
        return {
            "sectors": ["SaaS", "AI", "HR Tech"],
            "geography": ["CEE", "DACH"],
            "stages": ["Seed", "Series A"],
            "ticket_min": 300_000,
            "ticket_max": 2_000_000,
            "scoring": {
                "team_quality": 9,
                "tech_readiness": 8,
                "market_size": 9,
                "geography_fit": 10,
                "traction": 5,
                "ticket_fit": 5,
            },
            "flags": ["Flag if MRR < €20k", "Flag if hardware-intensive", "Flag if founder not technical"],
            "rejects": ["Reject if outside CEE", "Reject if no revenue (for Seed+)"],
            "notes": "We prefer founder-led companies, avoid government-heavy sectors.",
        }

    def build_prompt() -> Dict[str, str]:
        sys = (
            "You are configuring an inbound sourcing agent. The user provides a free-text investment thesis. "
            "Extract a STRICT JSON object only (no markdown, no commentary) matching this schema:\n"
            "{\n"
            '  "sectors": string[],\n'
            '  "geography": string[],\n'
            '  "stages": string[],\n'
            '  "ticket_min": number,   // euros\n'
            '  "ticket_max": number,   // euros\n'
            '  "scoring": {\n'
            '    "team_quality": number, "tech_readiness": number, "market_size": number,\n'
            '    "geography_fit": number, "traction": number, "ticket_fit": number\n'
            "  },\n"
            '  "flags": string[],\n'
            '  "rejects": string[],\n'
            '  "notes": string\n'
            "}\n"
            "Rules:\n"
            "- Return ONLY valid minified JSON. Do not include backticks or code fences.\n"
            "- Numbers must be integers 0..10 for scoring; ticket_min/max are integers in euros.\n"
            "- If unknown, infer sensible defaults; ensure arrays and fields exist."
        )
        usr = f"Free-text investment thesis:\n{thesis_text}"
        return {"system": sys, "user": usr}

    def parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        text = text.strip()
        # Remove code fences if present
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\\n|```$", "", text, flags=re.MULTILINE).strip()
        # Try direct JSON
        try:
            return json.loads(text)
        except Exception:
            # Try to extract the first {...} block
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = text[start : end + 1]
                try:
                    return json.loads(candidate)
                except Exception:
                    return None
        return None

    def normalize_merge(base_defaults: Dict[str, Any], parsed: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge parsed data with policy:
          - For list fields (sectors, geography, stages, flags, rejects):
              if parsed contains non-empty list -> use it
              else -> set to []
          - Ticket size: if parsed has valid ints (min<=max, non-negative) -> use
              else -> min=0, max=1_000_000
          - Scoring: use parsed numbers if present (clamped 0..10); otherwise keep defaults
          - Notes: use parsed string if present; otherwise empty string
        """
        result = dict(base_defaults)

        # Lists
        for key in ["sectors", "geography", "stages", "flags", "rejects"]:
            vals = []
            if isinstance(parsed, dict) and isinstance(parsed.get(key), list):
                vals = [str(x).strip() for x in parsed.get(key, []) if isinstance(x, (str, int, float)) and str(x).strip()]
            result[key] = vals

        # Ticket size
        def valid_int(x) -> Optional[int]:
            try:
                return int(x)
            except Exception:
                return None

        tmin = valid_int(parsed.get("ticket_min")) if isinstance(parsed, dict) else None
        tmax = valid_int(parsed.get("ticket_max")) if isinstance(parsed, dict) else None
        if isinstance(tmin, int) and isinstance(tmax, int) and tmin >= 0 and tmax >= 0 and tmax >= tmin:
            result["ticket_min"], result["ticket_max"] = tmin, tmax
        else:
            result["ticket_min"], result["ticket_max"] = 0, 1_000_000

        # Scoring
        def clamp010(v, fallback):
            try:
                iv = int(v)
                return max(0, min(10, iv))
            except Exception:
                return fallback

        parsed_scoring = parsed.get("scoring") if isinstance(parsed, dict) else {}
        base_scoring = base_defaults.get("scoring", {})
        result["scoring"] = {
            "team_quality": clamp010(parsed_scoring.get("team_quality"), base_scoring.get("team_quality", 9)),
            "tech_readiness": clamp010(parsed_scoring.get("tech_readiness"), base_scoring.get("tech_readiness", 8)),
            "market_size": clamp010(parsed_scoring.get("market_size"), base_scoring.get("market_size", 9)),
            "geography_fit": clamp010(parsed_scoring.get("geography_fit"), base_scoring.get("geography_fit", 10)),
            "traction": clamp010(parsed_scoring.get("traction"), base_scoring.get("traction", 5)),
            "ticket_fit": clamp010(parsed_scoring.get("ticket_fit"), base_scoring.get("ticket_fit", 5)),
        }

        # Notes
        if isinstance(parsed, dict) and isinstance(parsed.get("notes"), str):
            result["notes"] = parsed.get("notes", "")
        else:
            result["notes"] = ""

        return result

    base = defaults()
    prompt = build_prompt()
    try:
        # New SDK path (client provided)
        if client is not None:
            resp = client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]},
                ],
            )
            txt: Optional[str] = getattr(resp, "output_text", None)
            if not txt:
                try:
                    txt = resp.output[0].content[0].text.value  # type: ignore[attr-defined]
                except Exception:
                    txt = None
            data = parse_json_from_text(txt or "")
            return normalize_merge(base, data)

        # Legacy SDK path (no client available)
        import openai  # type: ignore

        openai.api_key = get_api_key()
        try:
            comp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]},
                ],
            )
        except Exception:
            comp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]},
                ],
            )

        content: Optional[str] = None
        try:
            content = comp["choices"][0]["message"]["content"]  # dict-like
        except Exception:
            try:
                content = comp.choices[0].message["content"]  # attribute + dict
            except Exception:
                try:
                    content = comp.choices[0].message.content  # attribute
                except Exception:
                    content = None

        data = parse_json_from_text(content or "")
        return normalize_merge(base, data)
    except Exception as e:
        # On failure, return base with fields emptied per policy
        fail = normalize_merge(base, {})
        fail["notes"] = f"⚠️ Error while calling AI: {e}"
        return fail
