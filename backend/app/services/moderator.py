from app.services.llm import moderate_call


def check_moderation(text: str, locale: str) -> dict:
    try:
        result = moderate_call(text)
        return {
            "passed": bool(result.get("passed", False)),
            "reasoning": result.get("reasoning", ""),
        }
    except Exception:
        return {
            "passed": False,
            "reasoning": "Moderation service error — fail-closed",
        }
