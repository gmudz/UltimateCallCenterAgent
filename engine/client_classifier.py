"""
Client Classifier Engine
Classifies clients into 4 personality types based on Arabic text analysis.
Types: Emotional (عاطفي), Analyst (محلل), Leader (قائد), Nice (لطيف)
"""

import re
from typing import Dict, List, Tuple

# Keywords and patterns for each client type (Arabic + transliterated)
CLIENT_PATTERNS = {
    "emotional": {
        "keywords": [
            "خايف", "خوف", "أخاف", "خسارة", "خسرت", "قلقان", "متردد",
            "ما أدري", "مش متأكد", "والله", "إن شاء الله", "يا ريت",
            "أحلم", "حلمي", "أبي أجرب", "حابة أجرب", "سمعت",
            "صديقي", "صديقتي", "قالوا لي", "حماس", "متحمس"
        ],
        "patterns": [
            r"خايف.*خسار",
            r"سمعت.*ناس",
            r"صديق.*ربح",
            r"أبي.*أجرب",
            r"حابة.*أجرب",
        ],
        "weight": 1.0,
        "strategy": {
            "ar": "التطمين وبناء الثقة → قصة نجاح واقعية → الحساب الإسلامي → دفع لطيف نحو الإيداع الأولي",
            "en": "Reassure → Success story → Islamic account → Gentle push to deposit",
            "tactics": [
                "استخدم لغة تطمينية: 'مفهوم خوفك، وهذا طبيعي'",
                "شارك قصة نجاح عميل مشابه",
                "ركّز على أدوات الحماية (Stop Loss)",
                "اقترح البدء بالحد الأدنى (250$)",
                "استغل الحماس قبل أن يبرد"
            ]
        }
    },
    "analyst": {
        "keywords": [
            "سبريد", "عمولة", "رسوم", "رافعة", "ترخيص", "مقارنة",
            "شركة ثانية", "عند شركة", "بالضبط", "كم", "نسبة",
            "تفاصيل", "أرقام", "إحصائيات", "بيانات", "XM", "eToro",
            "Exness", "منصة", "MT4", "MT5", "فروقات", "سحب", "إيداع"
        ],
        "patterns": [
            r"كم.*سبريد",
            r"شو.*رافعة",
            r"مقارن.*شرك",
            r"عند.*شركة.*ثاني",
            r"كم.*رسوم",
        ],
        "weight": 1.2,
        "strategy": {
            "ar": "تقديم أرقام دقيقة → مقارنة تنافسية → إبراز التراخيص → عرض تجريبي",
            "en": "Precise numbers → Competitive comparison → Licenses → Demo offer",
            "tactics": [
                "قدّم أرقام السبريد والرسوم بدقة",
                "قارن مباشرة مع المنافس الذي يذكره",
                "أبرز التراخيص الثلاثة (FSC, FSCA, VFSC)",
                "اقترح حساباً تجريبياً أولاً إذا لزم الأمر",
                "لا تبالغ — العميل المحلل يكتشف المبالغة فوراً"
            ]
        }
    },
    "leader": {
        "keywords": [
            "أنا أعرف", "أنا عارف", "ما أحتاج", "مش محتاج",
            "خبرة", "سنوات", "سنين", "بتداول من", "أتداول من",
            "أنا خبير", "أنا فاهم", "ما تعلمني", "أنا متداول",
            "عارف السوق", "فاهم السوق", "أكيد", "متأكد"
        ],
        "patterns": [
            r"أنا.*أعرف",
            r"أنا.*عارف",
            r"مش.*محتاج.*حد",
            r"بتداول.*من.*سن",
            r"أنا.*خبر",
        ],
        "weight": 1.1,
        "strategy": {
            "ar": "الموافقة على خبرته → إضافة قيمة جديدة → عرض حصري → ضغط زمني ذكي",
            "en": "Acknowledge expertise → Add new value → Exclusive offer → Smart urgency",
            "tactics": [
                "وافق على تحليله أولاً: 'تحليلك ممتاز'",
                "أضف معلومة لا يعرفها لتكسب احترامه",
                "لا تتحداه مباشرة أبداً",
                "قدّم عرضاً حصرياً 'للمتداولين المحترفين فقط'",
                "استخدم الضغط الزمني: 'العرض ينتهي اليوم'"
            ]
        }
    },
    "nice": {
        "keywords": [
            "إن شاء الله", "بشوف", "أفكر", "أسأل", "زوجي", "زوجتي",
            "عائلتي", "أحتاج وقت", "شوي", "بعدين", "لاحقاً",
            "ممكن", "يمكن", "بحاول", "بشاور", "أستشير",
            "حلو", "ممتاز", "عجبني", "حبيت"
        ],
        "patterns": [
            r"أحتاج.*وقت",
            r"أسأل.*زوج",
            r"أفكر.*شوي",
            r"بشوف.*بعدين",
            r"أستشير",
        ],
        "weight": 1.0,
        "strategy": {
            "ar": "تقدير لطفه → محفز زمني → ربط بفرصة حالية → التزام صغير",
            "en": "Appreciate → Time trigger → Link to current opportunity → Small commitment",
            "tactics": [
                "قدّر تفكيره: 'ممتاز إنك تاخذ وقتك'",
                "اربط بحدث اقتصادي: 'اليوم في فرصة على الذهب'",
                "اقترح التزاماً صغيراً: 'جرّب بـ 250$ فقط'",
                "حدد موعداً: 'أتواصل معك بكرة الساعة 10؟'",
                "لا تضغط — اللطيف يهرب من الضغط المباشر"
            ]
        }
    }
}


def classify_client(text_segments: List[str]) -> Dict:
    """
    Classify a client based on their text segments.
    Returns the detected type, confidence, and strategy.
    """
    combined_text = " ".join(text_segments).lower()
    scores = {"emotional": 0.0, "analyst": 0.0, "leader": 0.0, "nice": 0.0}

    for client_type, data in CLIENT_PATTERNS.items():
        # Keyword matching
        for keyword in data["keywords"]:
            count = combined_text.count(keyword)
            scores[client_type] += count * data["weight"]

        # Pattern matching
        for pattern in data["patterns"]:
            matches = re.findall(pattern, combined_text)
            scores[client_type] += len(matches) * 2.0 * data["weight"]

    total = sum(scores.values())
    if total == 0:
        return {
            "type": "unknown",
            "type_ar": "غير محدد",
            "confidence": 0.0,
            "scores": scores,
            "strategy": None,
            "icon": "❓"
        }

    # Normalize scores
    normalized = {k: v / total for k, v in scores.items()}
    best_type = max(normalized, key=normalized.get)
    confidence = normalized[best_type]

    type_labels = {
        "emotional": {"ar": "عاطفي", "icon": "💭"},
        "analyst": {"ar": "محلل", "icon": "📊"},
        "leader": {"ar": "قائد", "icon": "👑"},
        "nice": {"ar": "لطيف", "icon": "😊"}
    }

    return {
        "type": best_type,
        "type_ar": type_labels[best_type]["ar"],
        "confidence": round(confidence, 2),
        "scores": {k: round(v, 2) for k, v in normalized.items()},
        "strategy": CLIENT_PATTERNS[best_type]["strategy"],
        "icon": type_labels[best_type]["icon"]
    }


def get_realtime_classification(new_segment: str, history: List[str]) -> Dict:
    """
    Update classification with a new speech segment.
    Designed for real-time use during a call.
    """
    all_segments = history + [new_segment]
    result = classify_client(all_segments)
    result["segment_count"] = len(all_segments)
    result["latest_segment"] = new_segment
    return result
