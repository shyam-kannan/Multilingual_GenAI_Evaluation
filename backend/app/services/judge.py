from app.services.llm import judge_call

QUALITY_SYSTEM_PROMPT = """You are an LLM output quality judge. Evaluate the given output against the prompt and input.

Score three dimensions from 0.0 to 1.0:
- relevance: Does the output address the input given the prompt?
- completeness: Does the output fully answer what was asked?
- coherence: Is the output well-structured and logically consistent?

Respond ONLY with JSON:
{"relevance": float, "completeness": float, "coherence": float, "reasoning": "brief explanation"}"""

HALLUCINATION_SYSTEM_PROMPT = """You are a hallucination detector. Given a prompt template, user input, and LLM output, determine if the output contains fabricated information not supported by the input or prompt.

Score from 0.0 to 1.0 where:
- 0.0 = no hallucination, fully grounded
- 1.0 = completely fabricated

Respond ONLY with JSON:
{"score": float, "reasoning": "brief explanation of any hallucinated content"}"""


def score_quality(prompt_template: str, input_text: str, output: str, locale: str) -> dict:
    user_prompt = (
        f"Prompt template: {prompt_template}\n\n"
        f"User input: {input_text}\n\n"
        f"Locale: {locale}\n\n"
        f"LLM Output to evaluate:\n{output}"
    )
    result = judge_call(QUALITY_SYSTEM_PROMPT, user_prompt)

    relevance = float(result.get("relevance", 0))
    completeness = float(result.get("completeness", 0))
    coherence = float(result.get("coherence", 0))
    avg_score = round((relevance + completeness + coherence) / 3, 4)

    return {
        "score": avg_score,
        "reasoning": result.get("reasoning", ""),
        "details": {
            "relevance": relevance,
            "completeness": completeness,
            "coherence": coherence,
        },
    }


def score_hallucination(prompt_template: str, input_text: str, output: str, locale: str) -> dict:
    user_prompt = (
        f"Prompt template: {prompt_template}\n\n"
        f"User input: {input_text}\n\n"
        f"Locale: {locale}\n\n"
        f"LLM Output to check for hallucination:\n{output}"
    )
    result = judge_call(HALLUCINATION_SYSTEM_PROMPT, user_prompt)

    return {
        "score": float(result.get("score", 0)),
        "reasoning": result.get("reasoning", ""),
    }
