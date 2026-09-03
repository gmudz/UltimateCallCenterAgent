"""
AI Sales Copilot — Competitor Intelligence Engine
Detects competitor mentions and provides detailed comparison data.
Also generates follow-up messages (WhatsApp/SMS).
"""
import json
import os
import re
from typing import Dict, List, Optional
from datetime import datetime

# ---- Load Competitor Data ----
COMP_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'competitor_intelligence.json')
COMP_DATA = {}
try:
    with open(COMP_PATH, 'r', encoding='utf-8') as f:
        COMP_DATA = json.load(f)
except Exception as e:
    print(f"Warning: Could not load competitor data: {e}")


def detect_competitor(text: str) -> Optional[Dict]:
    """Detect if a competitor is mentioned in the text and return intelligence."""
    keywords = COMP_DATA.get("competitor_detection_keywords", {})
    competitors = COMP_DATA.get("competitors", {})

    for comp_id, kw_list in keywords.items():
        for kw in kw_list:
            if kw.lower() in text.lower():
                comp_info = competitors.get(comp_id)
                if not comp_info:
                    # Unknown competitor — still provide generic response
                    return {
                        "detected": True,
                        "competitor_id": comp_id,
                        "competitor_name": kw.upper(),
                        "logo": "🏢",
                        "has_details": False,
                        "generic_response": "عميلك ذكر منافس. ركّز على مزايانا: سبريد أقل، حساب إسلامي مجاني، أسهم خليجية، 3 تراخيص عالمية."
                    }
                # Build comparison cards
                comparisons = []
                for aspect, data in comp_info.get("comparison", {}).items():
                    labels = {
                        "spreads": "فروقات الأسعار",
                        "islamic_account": "الحساب الإسلامي",
                        "leverage": "الرافعة المالية",
                        "arab_stocks": "الأسهم الخليجية",
                        "support_arabic": "الدعم العربي",
                        "deposit_bonus": "بونص الإيداع",
                        "regulation": "التراخيص",
                        "education": "التعليم",
                        "ambassador": "السفير"
                    }
                    comparisons.append({
                        "aspect": labels.get(aspect, aspect),
                        "them": data.get("them", "—"),
                        "us": data.get("us", "—"),
                        "advantage": data.get("advantage", "—")
                    })

                return {
                    "detected": True,
                    "competitor_id": comp_id,
                    "competitor_name": comp_info["name"],
                    "logo": comp_info.get("logo", "🏢"),
                    "has_details": True,
                    "comparisons": comparisons,
                    "killing_points": comp_info.get("killing_points", [])
                }

    return None


# ---- Follow-Up Message Generator ----
FOLLOW_UP_TEMPLATES = {
    "interested_no_deposit": {
        "whatsapp": """مرحباً {client_name} 👋

تشرفنا بمحادثتك اليوم!

كما ناقشنا، عندنا فرص ممتازة في السوق الحين خاصة في {asset}. المحللين يتوقعون حركة كبيرة الأيام القادمة 📈

✅ حسابك جاهز مع بونص 20% على أول إيداع
✅ سبريد الذهب 0.25 — الأقل في السوق
✅ حساب إسلامي مجاني 100%

رابط فتح الحساب: [الرابط]

أنا هنا لأي سؤال — {agent_name}
📞 {agent_phone}""",
        "sms": "مرحباً {client_name}! تشرفنا بمحادثتك. حسابك جاهز مع بونص 20%. رابط فتح الحساب: [الرابط]. للاستفسار: {agent_phone}"
    },
    "hesitant_follow_up": {
        "whatsapp": """مرحباً {client_name} 👋

أتمنى تكون بخير! أنا {agent_name} من إيفست.

فكّرت في كلامنا وحبّيت أشاركك معلومة مهمة:

📊 {market_update}

اللي يهمني إنك تبدأ بشكل مريح:
• ابدأ بـ 250$ فقط — أقل من سعر عشاء
• تسحب فلوسك أي وقت خلال يوم عمل
• أنا معك خطوة بخطوة

متى أقدر أتصل فيك بكرة؟ 📞""",
        "sms": "مرحباً {client_name}! {market_update}. ابدأ بـ 250$ فقط مع بونص 20%. أتصل فيك بكرة؟ {agent_name} - {agent_phone}"
    },
    "objection_sharia": {
        "whatsapp": """مرحباً {client_name} 👋

بخصوص سؤالك المهم عن الشرعية:

✅ عندنا حساب إسلامي خالي 100% من الفوائد الربوية
✅ التداول = تجارة إلكترونية (بيع وشراء)
✅ أسهم حلال متاحة: أرامكو + المؤشر السعودي
✅ آلاف العملاء في الخليج يتداولون معنا وهم مرتاحين

لو حابب أشرحلك أكثر أو تجرب الحساب التجريبي المجاني — أنا موجود!

{agent_name}
📞 {agent_phone}"""
    },
    "post_deposit": {
        "whatsapp": """مبروك {client_name}! 🎉

تم فتح حسابك بنجاح مع بونص 20%! 💰

الخطوات القادمة:
1️⃣ حمّل تطبيق إيفست من App Store أو Google Play
2️⃣ سجّل دخول ببيانات حسابك
3️⃣ تابعني — بأرسلك أول توصية تداول خلال ساعة!

📚 رابط الأكاديمية التعليمية: [الرابط]
📊 أول هدف: تعلّم كيف تقرأ الشارت + تحط Stop Loss

أنا معك خطوة بخطوة! 🚀
{agent_name} — مدير حسابك الشخصي
📞 {agent_phone}"""
    }
}


def generate_follow_up(
    template_id: str,
    client_name: str = "",
    agent_name: str = "محمد",
    agent_phone: str = "+971xxxxxxxx",
    asset: str = "الذهب",
    market_update: str = "الذهب تحرك 20 دولار اليوم — فرصة ممتازة"
) -> Dict:
    """Generate follow-up messages from templates."""
    template = FOLLOW_UP_TEMPLATES.get(template_id, {})
    if not template:
        return {"error": "Template not found"}

    result = {}
    for channel, text in template.items():
        result[channel] = text.format(
            client_name=client_name or "العميل",
            agent_name=agent_name,
            agent_phone=agent_phone,
            asset=asset,
            market_update=market_update
        )

    return {
        "template_id": template_id,
        "messages": result,
        "generated_at": datetime.now().isoformat()
    }


def get_available_templates() -> List[Dict]:
    """Return list of available follow-up templates."""
    labels = {
        "interested_no_deposit": {"ar": "عميل مهتم — لم يودع", "icon": "🎯"},
        "hesitant_follow_up": {"ar": "متابعة عميل متردد", "icon": "⏰"},
        "objection_sharia": {"ar": "متابعة اعتراض الشرعية", "icon": "🕌"},
        "post_deposit": {"ar": "بعد الإيداع — ترحيب", "icon": "🎉"}
    }
    return [
        {"id": tid, "label_ar": labels.get(tid, {}).get("ar", tid), "icon": labels.get(tid, {}).get("icon", "📩"),
         "channels": list(template.keys())}
        for tid, template in FOLLOW_UP_TEMPLATES.items()
    ]
