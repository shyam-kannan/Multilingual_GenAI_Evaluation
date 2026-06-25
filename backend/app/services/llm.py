import json

import anthropic

from app.config import settings

LOCALE_INSTRUCTIONS = {
    "en-US": "Respond in American English.",
    "es-MX": "Responde en español mexicano.",
    "ar-SA": "أجب باللغة العربية (المملكة العربية السعودية).",
    "ja-JP": "日本語で回答してください。",
}


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def generate(prompt_template: str, input_text: str, locale: str) -> str:
    client = get_client()
    locale_instruction = LOCALE_INSTRUCTIONS.get(locale, "")
    system_message = f"{prompt_template}\n\n{locale_instruction}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_message,
        messages=[{"role": "user", "content": input_text}],
    )
    return response.content[0].text


def judge_call(system_prompt: str, user_prompt: str) -> dict:
    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise


def moderate_call(text: str) -> dict:
    client = get_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20241022",
        max_tokens=512,
        system=(
            "You are a content moderator. Analyze the following text for harmful, "
            "offensive, or inappropriate content. Respond with JSON: "
            '{"passed": true/false, "reasoning": "explanation"}'
        ),
        messages=[{"role": "user", "content": text}],
    )
    text_resp = response.content[0].text
    try:
        return json.loads(text_resp)
    except json.JSONDecodeError:
        start = text_resp.find("{")
        end = text_resp.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text_resp[start:end])
        raise
