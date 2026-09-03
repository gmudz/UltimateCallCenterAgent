"""
AI Sales Copilot — Agent Performance Scorer
Scores agent performance in real-time based on best-practice adherence.
"""
import re
from typing import Dict, List


# ---- Scoring Criteria ----
SCORING_RULES = {
    "used_client_name": {
        "label_ar": "استخدم اسم العميل",
        "icon": "👤",
        "weight": 10,
        "description": "ذكر اسم العميل في حديثه يزيد الثقة"
    },
    "asked_open_question": {
        "label_ar": "طرح سؤال مفتوح",
        "icon": "❓",
        "weight": 10,
        "triggers": [r"كيف.*تشوف", r"وش.*رأيك", r"شو.*تفضل", r"هل.*سبق", r"ليش.*تبحث", r"شو.*يهم"]
    },
    "used_3m_model": {
        "label_ar": "استخدم نموذج 3M",
        "icon": "📊",
        "weight": 15,
        "triggers": [r"تقرير.*وظائف", r"الفائدة", r"ذهب.*يتحرك", r"فرصة.*السوق", r"حركة.*متوقعة", r"نقطة.*ربح"]
    },
    "mentioned_risk_management": {
        "label_ar": "ذكر إدارة المخاطر",
        "icon": "🛡️",
        "weight": 12,
        "triggers": [r"وقف.*خسارة", r"stop.*loss", r"take.*profit", r"إدارة.*مخاطر", r"حماية.*رأس"]
    },
    "used_social_proof": {
        "label_ar": "استخدم الإثبات الاجتماعي",
        "icon": "👥",
        "weight": 10,
        "triggers": [r"كثير.*من.*عملائنا", r"ناس.*مثلك", r"عملاء.*ناجحين", r"قصة.*نجاح", r"عميل.*ربح"]
    },
    "addressed_objection": {
        "label_ar": "عالج اعتراض العميل",
        "icon": "⚔️",
        "weight": 15,
        "triggers": [r"أفهم.*خوفك", r"مفهوم.*سؤالك", r"حق.*لك", r"أقدّر.*حرصك", r"طبيعي.*تسأل"]
    },
    "offered_small_commitment": {
        "label_ar": "عرض التزام صغير",
        "icon": "🎯",
        "weight": 12,
        "triggers": [r"ابدأ.*ب.*250", r"مبلغ.*صغير", r"جرّب", r"بدون.*التزام", r"تسحب.*أي.*وقت"]
    },
    "created_urgency": {
        "label_ar": "خلق إلحاح زمني ذكي",
        "icon": "⏰",
        "weight": 8,
        "triggers": [r"ينتهي.*بكرة", r"عرض.*خاص", r"فرصة.*محدودة", r"السوق.*الحين", r"بونص"]
    },
    "used_closing_technique": {
        "label_ar": "استخدم تقنية إغلاق",
        "icon": "🔒",
        "weight": 15,
        "triggers": [r"أرسل.*رابط", r"نفتح.*حساب", r"تبدأ.*ب.*كم", r"250.*ولا.*500", r"أسهل.*شي.*تبدأ"]
    },
    "maintained_positive_tone": {
        "label_ar": "حافظ على نبرة إيجابية",
        "icon": "😊",
        "weight": 8,
        "triggers": [r"ممتاز", r"رائع", r"تمام", r"إن.*شاء.*الله", r"الحمدلله", r"مبروك"]
    }
}


class AgentScorer:
    """Scores agent performance in real-time during the call."""

    def __init__(self):
        self.criteria_met = set()
        self.agent_segments = []
        self.client_name = ""
        self.total_score = 0
        self.max_possible = sum(r["weight"] for r in SCORING_RULES.values())
        self.feedback_log = []

    def set_client_name(self, name: str):
        self.client_name = name

    def score_segment(self, text: str) -> Dict:
        """Score a single agent segment and return new achievements."""
        self.agent_segments.append(text)
        new_achievements = []

        # Check client name usage
        if self.client_name and self.client_name in text and "used_client_name" not in self.criteria_met:
            self.criteria_met.add("used_client_name")
            new_achievements.append("used_client_name")

        # Check all pattern-based rules
        for rule_id, rule in SCORING_RULES.items():
            if rule_id == "used_client_name":
                continue
            if rule_id in self.criteria_met:
                continue
            for pattern in rule.get("triggers", []):
                if re.search(pattern, text, re.IGNORECASE):
                    self.criteria_met.add(rule_id)
                    new_achievements.append(rule_id)
                    break

        # Calculate score
        self.total_score = sum(
            SCORING_RULES[c]["weight"] for c in self.criteria_met
        )

        # Build achievements list
        achievement_details = []
        for aid in new_achievements:
            rule = SCORING_RULES[aid]
            achievement_details.append({
                "id": aid,
                "label_ar": rule["label_ar"],
                "icon": rule["icon"],
                "points": rule["weight"]
            })
            self.feedback_log.append(f"+{rule['weight']} {rule['icon']} {rule['label_ar']}")

        return {
            "new_achievements": achievement_details,
            "total_score": self.total_score,
            "max_score": self.max_possible,
            "percentage": round(self.total_score / self.max_possible * 100) if self.max_possible > 0 else 0,
            "grade": self._get_grade(),
            "criteria_met": len(self.criteria_met),
            "total_criteria": len(SCORING_RULES),
            "all_met": [{"id": c, "label_ar": SCORING_RULES[c]["label_ar"], "icon": SCORING_RULES[c]["icon"]} for c in self.criteria_met]
        }

    def _get_grade(self) -> Dict:
        pct = round(self.total_score / self.max_possible * 100) if self.max_possible > 0 else 0
        if pct >= 85:
            return {"letter": "A+", "label_ar": "أداء استثنائي 🌟", "color": "#10b981"}
        elif pct >= 70:
            return {"letter": "A", "label_ar": "أداء ممتاز 🔥", "color": "#06b6d4"}
        elif pct >= 55:
            return {"letter": "B", "label_ar": "أداء جيد 👍", "color": "#6366f1"}
        elif pct >= 40:
            return {"letter": "C", "label_ar": "يحتاج تحسين ⚡", "color": "#f59e0b"}
        else:
            return {"letter": "D", "label_ar": "يحتاج تدريب 📚", "color": "#ef4444"}

    def get_final_report(self) -> Dict:
        """Generate final performance report at end of call."""
        missed = []
        for rule_id, rule in SCORING_RULES.items():
            if rule_id not in self.criteria_met:
                missed.append({
                    "id": rule_id,
                    "label_ar": rule["label_ar"],
                    "icon": rule["icon"],
                    "weight": rule["weight"]
                })

        return {
            "score": self.total_score,
            "max_score": self.max_possible,
            "percentage": round(self.total_score / self.max_possible * 100) if self.max_possible > 0 else 0,
            "grade": self._get_grade(),
            "achieved": [{"id": c, "label_ar": SCORING_RULES[c]["label_ar"], "icon": SCORING_RULES[c]["icon"], "weight": SCORING_RULES[c]["weight"]} for c in self.criteria_met],
            "missed": missed,
            "tips": self._generate_tips(missed),
            "total_segments": len(self.agent_segments)
        }

    def _generate_tips(self, missed: List) -> List[str]:
        tips = []
        for m in missed[:3]:
            tip_map = {
                "used_client_name": "حاول تذكر اسم العميل واستخدمه 3 مرات على الأقل خلال المكالمة",
                "asked_open_question": "اطرح أسئلة مفتوحة مثل 'وش أكثر شي يهمك؟' بدل أسئلة نعم/لا",
                "used_3m_model": "اربط كل حديث بنموذج 3M: خبر اقتصادي → سوق متأثر → حركة متوقعة + ربح",
                "mentioned_risk_management": "اذكر أدوات الحماية (Stop Loss, Take Profit) — العميل يحتاج يحس بالأمان",
                "used_social_proof": "استخدم قصص عملاء سابقين: 'كثير من عملائنا بدأوا مثلك وحققوا نتائج'",
                "addressed_objection": "عندما العميل يعترض، ابدأ بـ 'أفهمك' أو 'مفهوم خوفك' ثم أجب",
                "offered_small_commitment": "اعرض مبلغ صغير: '250 دولار بس — أقل من سعر عشاء'",
                "created_urgency": "اخلق إلحاح: 'البونص ينتهي بكرة' أو 'السوق فيه فرصة الحين'",
                "used_closing_technique": "في النهاية استخدم إغلاق: 'ممتاز، أرسلك الرابط — تبدأ بـ 250 ولا 500؟'",
                "maintained_positive_tone": "حافظ على نبرة إيجابية: 'ممتاز'، 'رائع'، 'إن شاء الله'"
            }
            tips.append(tip_map.get(m["id"], f"حاول تحقيق: {m['label_ar']}"))
        return tips
