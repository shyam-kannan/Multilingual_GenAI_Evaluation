"""
Seed script for the Multilingual GenAI Evaluation Gateway.

Creates:
  - 2 prompts ("customer-support" and "product-description"), each with 2 versions
  - Golden examples for all 4 locales per prompt
  - 24+ eval runs across locales and versions
  - 1 failing ar-SA demo (world-readiness fail: English output for Arabic locale)
  - 1 v1-vs-v2 quality regression for CI gate demo

Usage:
  python scripts/seed.py          (against running server at localhost:8000)
  python scripts/seed.py --url http://localhost:8000
"""

import argparse
import sys
import uuid
from datetime import datetime

import requests

DEFAULT_URL = "http://localhost:8000"


def api(base: str, method: str, path: str, json=None):
    r = getattr(requests, method)(f"{base}{path}", json=json)
    if r.status_code >= 400:
        print(f"  ERROR {method.upper()} {path}: {r.status_code} {r.text[:200]}")
        return None
    if r.status_code == 204:
        return {}
    return r.json()


def seed(base_url: str):
    print(f"Seeding against {base_url}...\n")

    # ── Health check ───────────────────────────────────────────────────
    r = requests.get(f"{base_url}/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print("Health check OK\n")

    # ── Prompt 1: customer-support ─────────────────────────────────────
    print("Creating prompt: customer-support")
    p1 = api(base_url, "post", "/api/prompts", {"name": "customer-support"})
    if not p1:
        sys.exit(1)
    p1_id = p1["id"]

    v1 = api(base_url, "post", f"/api/prompts/{p1_id}/versions", {
        "content": "You are a helpful customer support agent. Answer the customer's question clearly and concisely. Be polite and professional."
    })
    v1_id = v1["id"]
    api(base_url, "patch", f"/api/prompts/{p1_id}/versions/{v1_id}/labels", {"labels": ["production"]})
    api(base_url, "patch", f"/api/prompts/{p1_id}/versions/{v1_id}/activate", {})
    print(f"  v1 created: {v1_id} [production, active]")

    v2 = api(base_url, "post", f"/api/prompts/{p1_id}/versions", {
        "content": "You are a customer support agent. Answer briefly. Skip greetings. Just provide the answer."
    })
    v2_id = v2["id"]
    api(base_url, "patch", f"/api/prompts/{p1_id}/versions/{v2_id}/labels", {"labels": ["staging"]})
    print(f"  v2 created: {v2_id} [staging]")

    # ── Prompt 2: product-description ──────────────────────────────────
    print("\nCreating prompt: product-description")
    p2 = api(base_url, "post", "/api/prompts", {"name": "product-description"})
    p2_id = p2["id"]

    v3 = api(base_url, "post", f"/api/prompts/{p2_id}/versions", {
        "content": "Write a compelling product description for the given product. Highlight key features and benefits. Use persuasive language appropriate for the target locale."
    })
    v3_id = v3["id"]
    api(base_url, "patch", f"/api/prompts/{p2_id}/versions/{v3_id}/labels", {"labels": ["production"]})
    api(base_url, "patch", f"/api/prompts/{p2_id}/versions/{v3_id}/activate", {})
    print(f"  v1 created: {v3_id} [production, active]")

    v4 = api(base_url, "post", f"/api/prompts/{p2_id}/versions", {
        "content": "Describe the product. List features."
    })
    v4_id = v4["id"]
    api(base_url, "patch", f"/api/prompts/{p2_id}/versions/{v4_id}/labels", {"labels": ["staging"]})
    print(f"  v2 created: {v4_id} [staging]")

    # ── Golden examples ────────────────────────────────────────────────
    print("\nCreating golden examples...")
    goldens = [
        (p1_id, "en-US", "How do I reset my password?", "Navigate to Settings > Security > Reset Password and follow the prompts."),
        (p1_id, "es-MX", "¿Cómo restablezco mi contraseña?", "Vaya a Configuración > Seguridad > Restablecer contraseña y siga las instrucciones."),
        (p1_id, "ar-SA", "كيف أعيد تعيين كلمة المرور؟", "انتقل إلى الإعدادات > الأمان > إعادة تعيين كلمة المرور واتبع التعليمات."),
        (p1_id, "ja-JP", "パスワードをリセットするにはどうすればいいですか？", "設定 > セキュリティ > パスワードのリセットに移動し、指示に従ってください。"),
        (p2_id, "en-US", "Wireless noise-canceling headphones", "Premium wireless headphones with active noise cancellation."),
        (p2_id, "es-MX", "Auriculares inalámbricos con cancelación de ruido", "Auriculares inalámbricos premium con cancelación activa de ruido."),
        (p2_id, "ar-SA", "سماعات لاسلكية مع إلغاء الضوضاء", "سماعات لاسلكية فاخرة مع خاصية إلغاء الضوضاء النشط."),
        (p2_id, "ja-JP", "ワイヤレスノイズキャンセリングヘッドフォン", "アクティブノイズキャンセリング搭載のプレミアムワイヤレスヘッドフォン。"),
    ]
    for prompt_id, locale, input_text, expected in goldens:
        api(base_url, "post", "/api/golden-sets", {
            "prompt_id": prompt_id,
            "locale": locale,
            "input_text": input_text,
            "expected_output": expected,
        })
    print(f"  {len(goldens)} golden examples created")

    # ── Seed eval runs directly via DB ─────────────────────────────────
    # We insert eval runs directly to avoid needing a live Anthropic API key.
    print("\nCreating eval runs...")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Try connecting to the database
    import os
    db_url = os.environ.get("DATABASE_URL", "sqlite:///eval_gateway.db")
    print(f"  Using database: {db_url}")

    # Add backend to path for model imports
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "backend"))
    from app.database import Base
    from app.models.eval_run import EvalRun
    from app.models.ci_run import CIRun

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    eval_runs_data = [
        # ── customer-support v1 (production) — GOOD across locales ──────
        (v1_id, "en-US", "How do I reset my password?",
         "To reset your password, go to Settings > Security > Reset Password. Click the reset button and follow the email instructions. If you need further help, contact our support team.",
         0.92, "Highly relevant and complete response", 0.05, "No hallucination detected", True, "Content is appropriate",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}]}),

        (v1_id, "en-US", "What are your business hours?",
         "Our business hours are Monday through Friday, 9:00 AM to 6:00 PM EST. Weekend support is available via email with 24-hour response time.",
         0.88, "Complete and accurate response", 0.08, "Minor assumptions but grounded", True, "Appropriate",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}]}),

        (v1_id, "es-MX", "¿Cómo restablezco mi contraseña?",
         "Para restablecer su contraseña, vaya a Configuración > Seguridad > Restablecer contraseña. Haga clic en el botón de restablecimiento y siga las instrucciones del correo electrónico.",
         0.90, "Respuesta relevante y completa", 0.06, "Sin alucinación detectada", True, "Contenido apropiado",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}, {"check": "spanish_diacritics", "passed": True, "detail": "Spanish diacritics found"}]}),

        (v1_id, "es-MX", "¿Cuáles son sus horarios de atención?",
         "Nuestro horario de atención es de lunes a viernes, de 9:00 AM a 6:00 PM hora del centro de México. El soporte de fin de semana está disponible por correo electrónico.",
         0.85, "Buena respuesta localizada", 0.10, "Información precisa", True, "Apropiado",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}, {"check": "spanish_diacritics", "passed": True, "detail": "Spanish diacritics found"}]}),

        (v1_id, "ar-SA", "كيف أعيد تعيين كلمة المرور؟",
         "لإعادة تعيين كلمة المرور، انتقل إلى الإعدادات > الأمان > إعادة تعيين كلمة المرور. انقر على زر إعادة التعيين واتبع تعليمات البريد الإلكتروني.",
         0.91, "إجابة كاملة وملائمة", 0.04, "لا توجد معلومات ملفقة", True, "محتوى مناسب",
         True, {"passed": True, "checks": [{"check": "arabic_script", "passed": True, "detail": "Arabic script present"}, {"check": "rtl_direction", "passed": True, "detail": "RTL confirmed"}]}),

        (v1_id, "ar-SA", "ما هي ساعات العمل؟",
         "ساعات العمل لدينا من الأحد إلى الخميس، من الساعة ٩:٠٠ صباحاً حتى ٦:٠٠ مساءً بتوقيت المملكة العربية السعودية.",
         0.89, "إجابة دقيقة مع تكييف ثقافي", 0.07, "معلومات صحيحة", True, "مناسب",
         True, {"passed": True, "checks": [{"check": "arabic_script", "passed": True, "detail": "Arabic script present"}, {"check": "rtl_direction", "passed": True, "detail": "RTL confirmed"}]}),

        (v1_id, "ja-JP", "パスワードをリセットするにはどうすればいいですか？",
         "パスワードをリセットするには、設定 > セキュリティ > パスワードのリセットに移動してください。リセットボタンをクリックし、メールの指示に従ってください。",
         0.93, "完全で関連性の高い回答", 0.03, "ハルシネーションなし", True, "適切な内容",
         True, {"passed": True, "checks": [{"check": "cjk_script", "passed": True, "detail": "CJK script present"}]}),

        (v1_id, "ja-JP", "営業時間を教えてください",
         "営業時間は月曜日から金曜日、午前9時から午後6時（日本時間）です。週末はメールでのサポートをご利用いただけます。",
         0.87, "正確で完全な回答", 0.05, "情報は正確", True, "適切",
         True, {"passed": True, "checks": [{"check": "cjk_script", "passed": True, "detail": "CJK script present"}]}),

        # ── customer-support v2 (staging) — LOWER QUALITY (regression demo) ──
        (v2_id, "en-US", "How do I reset my password?",
         "Go to settings, reset password.",
         0.55, "Too brief, missing details", 0.12, "No hallucination but incomplete", True, "OK",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}]}),

        (v2_id, "en-US", "What are your business hours?",
         "9-6 weekdays.",
         0.45, "Extremely terse, lacks context", 0.15, "Incomplete information", True, "OK",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}]}),

        (v2_id, "es-MX", "¿Cómo restablezco mi contraseña?",
         "Vaya a configuración, restablezca.",
         0.50, "Demasiado breve", 0.10, "Sin alucinación", True, "OK",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}, {"check": "spanish_diacritics", "passed": True, "detail": "Spanish diacritics found"}]}),

        (v2_id, "ar-SA", "كيف أعيد تعيين كلمة المرور؟",
         "اذهب للإعدادات، أعد التعيين.",
         0.52, "إجابة مختصرة جداً", 0.09, "لا توجد معلومات ملفقة", True, "مناسب",
         True, {"passed": True, "checks": [{"check": "arabic_script", "passed": True, "detail": "Arabic script present"}]}),

        (v2_id, "ja-JP", "パスワードをリセットするにはどうすればいいですか？",
         "設定からリセットしてください。",
         0.48, "非常に簡潔すぎる", 0.08, "ハルシネーションなし", True, "適切",
         True, {"passed": True, "checks": [{"check": "cjk_script", "passed": True, "detail": "CJK script present"}]}),

        # ── FAILING ar-SA demo: English output for Arabic locale ────────
        (v1_id, "ar-SA", "ما هي سياسة الإرجاع؟",
         "Our return policy allows returns within 30 days of purchase. Items must be in original condition with receipt.",
         0.75, "Response is relevant but in wrong language", 0.10, "No hallucination", True, "Content is appropriate",
         False, {"passed": False, "checks": [
             {"check": "arabic_script", "passed": False, "detail": "No Arabic script detected"},
             {"check": "rtl_direction", "passed": False, "detail": "No RTL markers or Arabic script detected"},
             {"check": "untranslated_strings", "passed": False, "latin_ratio": 1.0, "detail": "Latin script ratio: 100.0% — likely untranslated content"}
         ]}),

        # ── product-description v1 — GOOD ──────────────────────────────
        (v3_id, "en-US", "Wireless noise-canceling headphones",
         "Experience audio perfection with our Premium Wireless Headphones. Featuring advanced active noise cancellation technology, these headphones deliver crystal-clear sound in any environment. With 30-hour battery life and ultra-comfortable memory foam ear cushions, they're designed for all-day listening pleasure. Compatible with all Bluetooth 5.0 devices.",
         0.95, "Excellent product description with key features", 0.08, "Slight embellishment but acceptable for marketing", True, "Appropriate",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}]}),

        (v3_id, "es-MX", "Auriculares inalámbricos con cancelación de ruido",
         "Experimente la perfección del audio con nuestros Auriculares Inalámbricos Premium. Con tecnología avanzada de cancelación activa de ruido, estos auriculares ofrecen un sonido cristalino en cualquier entorno. Con 30 horas de batería y almohadillas de espuma viscoelástica ultra cómodas, están diseñados para escuchar todo el día.",
         0.93, "Excelente descripción localizada", 0.07, "Aceptable para marketing", True, "Apropiado",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}, {"check": "spanish_diacritics", "passed": True, "detail": "Spanish diacritics found"}]}),

        (v3_id, "ar-SA", "سماعات لاسلكية مع إلغاء الضوضاء",
         "استمتع بالكمال الصوتي مع سماعاتنا اللاسلكية الفاخرة. تتميز بتقنية إلغاء الضوضاء النشط المتقدمة، وتوفر هذه السماعات صوتاً نقياً في أي بيئة. مع عمر بطارية يصل إلى ٣٠ ساعة ووسائد أذن من الإسفنج.",
         0.90, "وصف منتج ممتاز بالعربية", 0.06, "مقبول للتسويق", True, "مناسب",
         True, {"passed": True, "checks": [{"check": "arabic_script", "passed": True, "detail": "Arabic script present"}, {"check": "rtl_direction", "passed": True, "detail": "RTL confirmed"}]}),

        (v3_id, "ja-JP", "ワイヤレスノイズキャンセリングヘッドフォン",
         "プレミアムワイヤレスヘッドフォンで完璧なオーディオ体験を。先進のアクティブノイズキャンセリング技術を搭載し、どんな環境でもクリアなサウンドをお届けします。30時間のバッテリー寿命と超快適なメモリーフォームイヤークッションで、一日中快適にお楽しみいただけます。",
         0.94, "優れた製品説明", 0.05, "マーケティングとして許容範囲", True, "適切",
         True, {"passed": True, "checks": [{"check": "cjk_script", "passed": True, "detail": "CJK script present"}]}),

        # ── product-description v2 — LOWER QUALITY ─────────────────────
        (v4_id, "en-US", "Wireless noise-canceling headphones",
         "Headphones. Noise canceling. Wireless. Battery lasts long.",
         0.40, "Too terse for product description", 0.20, "No fabrication but uninformative", True, "OK",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}]}),

        (v4_id, "es-MX", "Auriculares inalámbricos con cancelación de ruido",
         "Auriculares. Cancelación de ruido. Inalámbricos. Batería dura mucho.",
         0.42, "Demasiado escueto para una descripción", 0.18, "Sin fabricación", True, "OK",
         True, {"passed": True, "checks": [{"check": "script", "passed": True, "detail": "Latin script present"}, {"check": "spanish_diacritics", "passed": True, "detail": "Spanish diacritics found"}]}),

        (v4_id, "ar-SA", "سماعات لاسلكية مع إلغاء الضوضاء",
         "سماعات. إلغاء ضوضاء. لاسلكية. بطارية طويلة.",
         0.38, "وصف مختصر جداً", 0.15, "بدون تلفيق", True, "مناسب",
         True, {"passed": True, "checks": [{"check": "arabic_script", "passed": True, "detail": "Arabic script present"}]}),

        (v4_id, "ja-JP", "ワイヤレスノイズキャンセリングヘッドフォン",
         "ヘッドフォン。ノイズキャンセリング。ワイヤレス。バッテリー長持ち。",
         0.43, "製品説明として不十分", 0.12, "捏造なし", True, "適切",
         True, {"passed": True, "checks": [{"check": "cjk_script", "passed": True, "detail": "CJK script present"}]}),
    ]

    run_count = 0
    for row in eval_runs_data:
        (version_id, locale, input_text, llm_output,
         quality_score, quality_reasoning, hallucination_score, hallucination_reasoning,
         moderation_passed, moderation_reasoning, world_readiness_passed, world_readiness_details) = row

        overall_passed = (
            quality_score >= 0.7
            and hallucination_score <= 0.3
            and moderation_passed
            and world_readiness_passed
        )

        eval_run = EvalRun(
            prompt_version_id=version_id,
            locale=locale,
            input_text=input_text,
            llm_output=llm_output,
            quality_score=quality_score,
            quality_reasoning=quality_reasoning,
            hallucination_score=hallucination_score,
            hallucination_reasoning=hallucination_reasoning,
            moderation_passed=moderation_passed,
            moderation_reasoning=moderation_reasoning,
            world_readiness_passed=world_readiness_passed,
            world_readiness_details=world_readiness_details,
            overall_passed=overall_passed,
        )
        db.add(eval_run)
        run_count += 1

    db.commit()
    print(f"  {run_count} eval runs created")

    # ── CI runs ────────────────────────────────────────────────────────
    print("\nCreating CI runs...")

    # CI run 1: customer-support v2 vs v1 — REGRESSION (quality dropped)
    ci1 = CIRun(
        prompt_id=p1_id,
        candidate_version_id=v2_id,
        baseline_version_id=v1_id,
        status="failed",
        regressions=[
            {"locale": "en-US", "metric": "quality", "baseline": 0.90, "candidate": 0.50, "delta": -0.40},
            {"locale": "es-MX", "metric": "quality", "baseline": 0.875, "candidate": 0.50, "delta": -0.375},
            {"locale": "ja-JP", "metric": "quality", "baseline": 0.90, "candidate": 0.48, "delta": -0.42},
        ],
        details={
            "en-US": {"quality": 0.50, "hallucination": 0.135, "run_count": 2},
            "es-MX": {"quality": 0.50, "hallucination": 0.10, "run_count": 1},
            "ar-SA": {"quality": 0.52, "hallucination": 0.09, "run_count": 1},
            "ja-JP": {"quality": 0.48, "hallucination": 0.08, "run_count": 1},
        },
    )
    db.add(ci1)

    # CI run 2: product-description v2 vs v1 — REGRESSION
    ci2 = CIRun(
        prompt_id=p2_id,
        candidate_version_id=v4_id,
        baseline_version_id=v3_id,
        status="failed",
        regressions=[
            {"locale": "en-US", "metric": "quality", "baseline": 0.95, "candidate": 0.40, "delta": -0.55},
            {"locale": "ar-SA", "metric": "quality", "baseline": 0.90, "candidate": 0.38, "delta": -0.52},
        ],
        details={
            "en-US": {"quality": 0.40, "hallucination": 0.20, "run_count": 1},
            "es-MX": {"quality": 0.42, "hallucination": 0.18, "run_count": 1},
            "ar-SA": {"quality": 0.38, "hallucination": 0.15, "run_count": 1},
            "ja-JP": {"quality": 0.43, "hallucination": 0.12, "run_count": 1},
        },
    )
    db.add(ci2)

    # CI run 3: customer-support v1 — PASS (no baseline / initial)
    ci3 = CIRun(
        prompt_id=p1_id,
        candidate_version_id=v1_id,
        baseline_version_id=None,
        status="passed",
        regressions=[],
        details={
            "en-US": {"quality": 0.90, "hallucination": 0.065, "run_count": 2},
            "es-MX": {"quality": 0.875, "hallucination": 0.08, "run_count": 2},
            "ar-SA": {"quality": 0.90, "hallucination": 0.055, "run_count": 2},
            "ja-JP": {"quality": 0.90, "hallucination": 0.04, "run_count": 2},
        },
    )
    db.add(ci3)

    db.commit()
    print("  3 CI runs created (1 passed, 2 failed with regressions)")

    # ── Summary ────────────────────────────────────────────────────────
    print(f"""
Seed complete!
  Prompts:        2
  Versions:       4 (2 per prompt)
  Golden examples: {len(goldens)}
  Eval runs:      {run_count}
  CI runs:        3

Notable entries:
  - FAILING ar-SA: customer-support v1 returned English for Arabic locale (world-readiness fail)
  - REGRESSION: customer-support v2 quality dropped ~40% vs v1 across all locales
  - REGRESSION: product-description v2 quality dropped ~50% vs v1

Open http://localhost:5173 to view the dashboard.
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args()
    seed(args.url)
