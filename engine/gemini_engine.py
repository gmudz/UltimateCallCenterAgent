"""
AI Sales Copilot — Gemini AI Engine
Uses Google Gemini to generate professional sales responses in Arabic.
"""
import os
import json
from typing import Optional, Dict

# API key storage path
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'gemini_config.json')

# System prompt — STRICTLY answers from training files only
SYSTEM_PROMPT = """أنت مساعد ذكاء اصطناعي لموظف مبيعات. مهمتك تولّد ردود احترافية بالعربية **فقط من المعلومات الموجودة في ملفات التدريب المرفقة**.

## القاعدة الأهم:
- أجب **فقط** بناءً على "معلومات من ملفات التدريب" الموجودة في السياق أدناه
- **لا تختلق** أي معلومة غير موجودة في ملفات التدريب
- **لا تضف** أرقام أو حقائق أو ادعاءات من عندك
- إذا لم تجد إجابة في المعلومات المرفقة → قل: "لا تتوفر لدي معلومات حول هذا الموضوع في ملفات التدريب"

## أسلوب الرد:
1. الرد بالعربية، مختصر (2-4 جمل)، جاهز للنسخ
2. اكتب كأنك الموظف نفسه — لا تذكر أنك ذكاء اصطناعي
3. ابدأ بالموافقة المبدئية ("سؤال ممتاز..."، "أقدّر اهتمامك...")
4. اختم بسؤال ينقل الحوار للخطوة التالية

## فن قيادة الحديث:
- استخدم تقنية Feel-Felt-Found عند المعارضات
- لا تدافع — اسأل ثم عالج السبب الحقيقي
- صِغ الرد بشكل يبني ثقة العميل

## تذكير: كل كلمة في ردك يجب أن تكون مبنية على ملفات التدريب فقط."""


def get_api_key() -> Optional[str]:
    """Get stored API key."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                key = config.get('api_key', '').strip()
                if key:
                    return key
        except Exception:
            pass
    return os.environ.get('GEMINI_API_KEY')


def save_api_key(key: str) -> Dict:
    """Save API key."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump({'api_key': key}, f)
    return {"success": True}


def is_configured() -> bool:
    """Check if Gemini is configured."""
    return bool(get_api_key())


async def generate_response(
    client_text: str,
    rag_context: str = "",
    client_type: str = "unknown",
    stage: str = "presentation",
    mood: str = "neutral",
    conversation_history: list = None
) -> Optional[Dict]:
    """
    Generate a sales response using Gemini.
    Returns None if Gemini is not configured or fails.
    """
    api_key = get_api_key()
    if not api_key:
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        # Build context prompt
        context_parts = []
        has_training_data = rag_context and rag_context != "لم يتم العثور على معلومات ذات صلة."

        # If no training data found → return "no data" card without calling Gemini
        if not has_training_data:
            return {
                "type": "gemini_response",
                "icon": "⚠️",
                "title_ar": "⚠️ لا توجد معلومات",
                "text": "لا تتوفر معلومات حول هذا الموضوع في ملفات التدريب. ارفع ملفات تحتوي على إجابات لهذا النوع من الأسئلة.",
                "priority": "normal",
                "copyable": False,
                "model": "no-data"
            }

        context_parts.append(f"معلومات من ملفات التدريب (أجب فقط بناءً على هذه المعلومات!):\n{rag_context}")
        if client_type != "unknown":
            type_labels = {
                "emotional": "عاطفي — يحتاج تعاطف وتشجيع",
                "analyst": "تحليلي — يحتاج أرقام وحقائق",
                "leader": "قائد — يحتاج يحس بالسيطرة والتميز",
                "nice": "ودود — يحتاج علاقة شخصية ودفء"
            }
            context_parts.append(f"نوع العميل: {type_labels.get(client_type, client_type)}")
        stage_labels = {
            "introduction": "التعارف", "needs_discovery": "اكتشاف الاحتياجات",
            "presentation": "العرض", "objection_handling": "معالجة اعتراض",
            "closing": "الإغلاق"
        }
        context_parts.append(f"المرحلة: {stage_labels.get(stage, stage)}")
        mood_labels = {"interested": "مهتم", "hesitant": "متردد", "resistant": "رافض", "aggressive": "عدواني"}
        if mood != "neutral":
            context_parts.append(f"حالة العميل: {mood_labels.get(mood, mood)}")

        # Recent conversation
        if conversation_history and len(conversation_history) > 0:
            recent = conversation_history[-6:]
            history_text = "\n".join([f"{'العميل' if s['speaker']=='client' else 'الموظف'}: {s['text']}" for s in recent])
            context_parts.append(f"آخر المحادثة:\n{history_text}")

        context_str = "\n\n".join(context_parts) if context_parts else ""

        user_prompt = f"""العميل قال: "{client_text}"

{context_str}

اكتب رداً احترافياً بناءً فقط على معلومات ملفات التدريب أعلاه. الرد مختصر (2-4 جمل) وجاهز للنسخ. اختم بسؤال. لا تضف أي معلومة غير موجودة في ملفات التدريب."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.7,
                "max_output_tokens": 300
            }
        )

        response_text = response.text.strip() if response.text else None
        if not response_text:
            return None

        return {
            "type": "gemini_response",
            "icon": "✨",
            "title_ar": "✨ اقتراح Gemini AI",
            "text": response_text,
            "priority": "critical",
            "copyable": True,
            "model": "gemini-2.0-flash"
        }

    except Exception as e:
        print(f"Gemini error: {e}")
        return None
