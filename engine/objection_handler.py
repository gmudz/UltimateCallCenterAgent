"""
Objection Handler Engine (Battle Cards)
Detects client objections in Arabic and provides response strategies.
"""

import re
from typing import Dict, List, Optional

BATTLE_CARDS = {
    "sharia": {
        "id": "sharia",
        "title_ar": "اعتراض الشرعية",
        "title_en": "Sharia Compliance Objection",
        "icon": "🕌",
        "severity": "high",
        "triggers": [
            "حلال", "حرام", "شرعي", "دين", "ربا", "ربوي",
            "فوائد", "إسلامي", "مشروع", "شبهة", "فتوى",
            "يجوز", "ما يجوز", "محرم", "الشيخ", "العلماء"
        ],
        "trigger_patterns": [
            r"حلال.*حرام",
            r"هل.*حلال",
            r"هل.*حرام",
            r"شو.*حكم.*الشرع",
            r"فيه.*شبه",
        ],
        "response_points": [
            {
                "point": "الحساب الإسلامي",
                "detail": "نوفّر حساباً إسلامياً خالياً تماماً من الفوائد الربوية (السواب). لا يتم خصم أي رسوم تبييت.",
                "icon": "✅"
            },
            {
                "point": "طبيعة التداول",
                "detail": "التداول في أساسه عملية بيع وشراء إلكترونية — تجارة مشروعة. أنت تشتري بسعر وتبيع بسعر آخر.",
                "icon": "📈"
            },
            {
                "point": "أسهم حلال",
                "detail": "نوفّر تداول أسهم شركات متوافقة مع الشريعة مثل أرامكو السعودية والمؤشر السعودي تداول.",
                "icon": "🏢"
            },
            {
                "point": "الشفافية الكاملة",
                "detail": "جميع الرسوم والتكاليف معروضة بشفافية تامة قبل فتح أي صفقة. لا توجد رسوم مخفية.",
                "icon": "🔍"
            }
        ]
    },
    "fraud": {
        "id": "fraud",
        "title_ar": "اعتراض الخوف من النصب",
        "title_en": "Fraud Fear Objection",
        "icon": "🛡️",
        "severity": "high",
        "triggers": [
            "نصب", "نصابة", "نصابين", "احتيال", "محتال",
            "سرقة", "يسرق", "ثقة", "ما أثق", "مش واثق",
            "مضمون", "ضمان", "أموالي", "فلوسي", "خطر",
            "مرخص", "ترخيص", "قانوني", "رقابة"
        ],
        "trigger_patterns": [
            r"خايف.*نصب",
            r"شركة.*نصابة",
            r"فلوس.*ضايع",
            r"أموال.*مضمون",
            r"مش.*واثق",
        ],
        "response_points": [
            {
                "point": "التراخيص الدولية",
                "detail": "مرخصون من 3 هيئات رقابية عالمية: FSC (هيئة الخدمات المالية)، FSCA (جنوب أفريقيا)، VFSC (فانواتو).",
                "icon": "🏛️"
            },
            {
                "point": "حماية الأموال",
                "detail": "أموال العملاء محفوظة في حسابات بنكية منفصلة تماماً عن أموال الشركة التشغيلية.",
                "icon": "🔒"
            },
            {
                "point": "الأمان التقني",
                "detail": "النظام محمي بتشفير SSL 256-bit ورمز OTP يصل لهاتفك مباشرة عند كل عملية.",
                "icon": "🔐"
            },
            {
                "point": "سفراء موثوقون",
                "detail": "سفير الشركة هو مهند الوادية (ذئب العقارات) — لن يربط اسمه بشركة غير موثوقة.",
                "icon": "⭐"
            }
        ]
    },
    "loss": {
        "id": "loss",
        "title_ar": "اعتراض الخوف من الخسارة",
        "title_en": "Loss Fear Objection",
        "icon": "📉",
        "severity": "medium",
        "triggers": [
            "خسارة", "خسرت", "خسران", "أخسر", "ضياع",
            "رأس المال", "مبلغ كبير", "مخاطرة", "مخاطر",
            "ناس خسرت", "خسر فلوسه", "صفر", "انهيار"
        ],
        "trigger_patterns": [
            r"خايف.*أخسر",
            r"ناس.*خسر",
            r"رأس.*مال.*ضاع",
            r"خسارة.*كل",
        ],
        "response_points": [
            {
                "point": "وقف الخسارة (Stop Loss)",
                "detail": "أداة تغلق صفقتك تلقائياً عند وصول الخسارة لمستوى تحدده أنت مسبقاً. أنت تتحكم بالمخاطر.",
                "icon": "🛑"
            },
            {
                "point": "جني الأرباح (Take Profit)",
                "detail": "أداة تقفل صفقتك تلقائياً عند تحقيق الربح المطلوب. تحمي أرباحك حتى لو لم تكن أمام الشاشة.",
                "icon": "🎯"
            },
            {
                "point": "إدارة المخاطر",
                "detail": "لا نتداول عشوائياً — كل صفقة مبنية على تحليل فني وأساسي مع نسبة مخاطرة محسوبة.",
                "icon": "📊"
            },
            {
                "point": "البداية الصغيرة",
                "detail": "ابدأ بـ 250 دولار فقط كحد أدنى. لا تستثمر أكثر مما يمكنك تحمّل خسارته.",
                "icon": "💰"
            }
        ]
    },
    "competitor": {
        "id": "competitor",
        "title_ar": "مقارنة مع المنافسين",
        "title_en": "Competitor Comparison",
        "icon": "⚔️",
        "severity": "medium",
        "triggers": [
            "شركة ثانية", "شركة تانية", "عند شركة", "شركة أخرى",
            "XM", "eToro", "Exness", "AvaTrade", "Plus500",
            "منافس", "أفضل شركة", "أحسن شركة", "بديل"
        ],
        "trigger_patterns": [
            r"عند.*شركة",
            r"أفضل.*من",
            r"ليش.*عندكم",
            r"شو.*الفرق",
        ],
        "response_points": [
            {
                "point": "فروقات أسعار تنافسية",
                "detail": "السبريد عندنا يبدأ من 0.0 نقطة على الحساب الممتاز — من الأقل في السوق.",
                "icon": "💹"
            },
            {
                "point": "دعم عربي شامل",
                "detail": "فريق دعم عربي متخصص على مدار الساعة + أكاديمية تعليمية باللغة العربية.",
                "icon": "🇸🇦"
            },
            {
                "point": "سحب سريع",
                "detail": "معالجة طلبات السحب خلال 1-3 أيام عمل فقط — أسرع من معظم المنافسين.",
                "icon": "⚡"
            },
            {
                "point": "حساب إسلامي حقيقي",
                "detail": "حسابنا الإسلامي بدون أي رسوم تبييت — وليس مجرد تسمية تسويقية.",
                "icon": "✨"
            }
        ]
    },
    "timing": {
        "id": "timing",
        "title_ar": "تأجيل القرار",
        "title_en": "Decision Delay",
        "icon": "⏰",
        "severity": "low",
        "triggers": [
            "بعدين", "لاحقاً", "مش الحين", "مو الحين",
            "أفكر", "بفكر", "بشوف", "أشاور", "أستشير",
            "الأسبوع الجاي", "بكرة", "غداً", "وقت ثاني"
        ],
        "trigger_patterns": [
            r"أفكر.*بعدين",
            r"أشاور.*بعدين",
            r"مش.*الوقت",
        ],
        "response_points": [
            {
                "point": "الفرصة الحالية",
                "detail": "السوق فيه فرصة قوية اليوم — تأخير القرار قد يعني تفويت ربح محتمل.",
                "icon": "🔥"
            },
            {
                "point": "لا التزام كبير",
                "detail": "ابدأ بـ 250$ فقط كتجربة. إذا لم يعجبك، يمكنك سحب أموالك في أي وقت.",
                "icon": "🤏"
            },
            {
                "point": "الدعم المستمر",
                "detail": "أنا شخصياً سأساعدك في أول صفقة وأرافقك خطوة بخطوة.",
                "icon": "🤝"
            },
            {
                "point": "حجز الموعد",
                "detail": "إذا تفضّل وقت آخر، خلّيني أحجز لك موعد مكالمة ثانية بكرة — ما ندعك تضيع.",
                "icon": "📅"
            }
        ]
    }
}


def detect_objections(text: str) -> List[Dict]:
    """
    Detect objections in Arabic text and return matching battle cards.
    """
    detected = []
    text_lower = text.lower()

    for card_id, card in BATTLE_CARDS.items():
        score = 0

        # Check keyword triggers
        for trigger in card["triggers"]:
            if trigger.lower() in text_lower:
                score += 1

        # Check patterns  
        for pattern in card["trigger_patterns"]:
            if re.search(pattern, text_lower):
                score += 2

        if score > 0:
            detected.append({
                "card": card,
                "relevance_score": score,
                "triggered_in": text[:80] + "..." if len(text) > 80 else text
            })

    # Sort by relevance
    detected.sort(key=lambda x: x["relevance_score"], reverse=True)
    return detected


def get_battle_card(card_id: str) -> Optional[Dict]:
    """Get a specific battle card by ID."""
    return BATTLE_CARDS.get(card_id)


def get_all_cards() -> Dict:
    """Return all available battle cards."""
    return BATTLE_CARDS
