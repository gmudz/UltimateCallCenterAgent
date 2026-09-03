"""
Compliance Monitor Engine
Real-time monitoring for regulatory violations during sales calls.
"""

import re
from typing import Dict, List
from datetime import datetime

# Compliance rules — things agents MUST NOT say
VIOLATION_RULES = {
    "guaranteed_profit": {
        "id": "guaranteed_profit",
        "title_ar": "⛔ وعد بأرباح مضمونة",
        "title_en": "Guaranteed Profit Promise",
        "severity": "critical",
        "description_ar": "يُمنع وعد العميل بأرباح محددة أو مضمونة. التداول ينطوي على مخاطر.",
        "triggers": [
            "أضمن لك", "مضمون", "ربح أكيد", "ربح مضمون",
            "100%", "بدون خسارة", "ما في خسارة", "مستحيل تخسر",
            "مؤكد", "أكيد تربح", "بتربح أكيد"
        ],
        "patterns": [
            r"أضمن.*ربح",
            r"مضمون.*ربح",
            r"مستحيل.*خسار",
            r"أكيد.*تربح",
            r"100.*بال.*مية",
        ]
    },
    "false_identity": {
        "id": "false_identity",
        "title_ar": "⛔ استخدام هوية مزيفة",
        "title_en": "False Identity",
        "severity": "critical",
        "description_ar": "يُمنع استخدام أسماء أو صفات مزيفة أثناء المكالمة.",
        "triggers": [
            "أنا المدير", "أنا مدير", "اسمي مش",
            "دكتور", "مهندس", "محامي"
        ],
        "patterns": [
            r"أنا.*مدير.*عام",
            r"اسمي.*مش",
        ]
    },
    "religious_oath": {
        "id": "religious_oath",
        "title_ar": "⚠️ حلف ديني غير مناسب",
        "title_en": "Inappropriate Religious Oath",
        "severity": "warning",
        "description_ar": "تجنّب الحلف بالله أو القسم الديني لإقناع العميل.",
        "triggers": [
            "والله العظيم", "بالله عليك", "أقسم بالله",
            "والله ما بكذب", "حلفان بالله"
        ],
        "patterns": [
            r"والله.*أضمن",
            r"أقسم.*بالله",
            r"والله.*العظيم",
        ]
    },
    "pressure_tactics": {
        "id": "pressure_tactics",
        "title_ar": "⚠️ ضغط مفرط على العميل",
        "title_en": "Excessive Pressure",
        "severity": "warning",
        "description_ar": "تجنّب الضغط المفرط أو التخويف لإجبار العميل على الإيداع.",
        "triggers": [
            "لازم تودع الحين", "لازم الحين", "راح تخسر الفرصة",
            "إذا ما ودعت", "آخر فرصة", "ما في وقت"
        ],
        "patterns": [
            r"لازم.*الحين",
            r"آخر.*فرصة.*عمرك",
            r"إذا.*ما.*ودع",
        ]
    },
    "competitor_badmouthing": {
        "id": "competitor_badmouthing",
        "title_ar": "⚠️ التشهير بالمنافسين",
        "title_en": "Competitor Badmouthing",
        "severity": "warning",
        "description_ar": "يُمنع التشهير بالمنافسين أو اتهامهم بالنصب بشكل مباشر.",
        "triggers": [
            "نصابين", "شركة نصابة", "حرامية",
            "سرّاقين", "ما تثق فيهم"
        ],
        "patterns": [
            r"شرك.*نصاب",
            r"كلهم.*حرام",
        ]
    },
    "unauthorized_advice": {
        "id": "unauthorized_advice",
        "title_ar": "⚠️ نصيحة استثمارية غير مخوّلة",
        "title_en": "Unauthorized Investment Advice",
        "severity": "warning",
        "description_ar": "يُمنع تقديم نصائح استثمارية محددة (اشتري/بيع). يمكن فقط عرض السيناريوهات.",
        "triggers": [
            "لازم تشتري", "بيع الحين", "اشتري الذهب",
            "أنصحك تشتري", "أنصحك تبيع", "استثمر في"
        ],
        "patterns": [
            r"لازم.*تشتري",
            r"أنصحك.*تشتري",
            r"بيع.*الحين",
        ]
    }
}


class ComplianceMonitor:
    """Real-time compliance monitoring for agent calls."""

    def __init__(self):
        self.violations_log: List[Dict] = []
        self.warning_count = 0
        self.critical_count = 0

    def check_text(self, text: str, speaker: str = "agent") -> List[Dict]:
        """
        Check a text segment for compliance violations.
        Only checks agent speech (not client speech).
        """
        if speaker != "agent":
            return []

        violations = []
        text_lower = text.lower()

        for rule_id, rule in VIOLATION_RULES.items():
            triggered = False
            trigger_word = ""

            # Check keywords
            for trigger in rule["triggers"]:
                if trigger.lower() in text_lower:
                    triggered = True
                    trigger_word = trigger
                    break

            # Check patterns
            if not triggered:
                for pattern in rule["patterns"]:
                    match = re.search(pattern, text_lower)
                    if match:
                        triggered = True
                        trigger_word = match.group()
                        break

            if triggered:
                violation = {
                    "rule_id": rule_id,
                    "title_ar": rule["title_ar"],
                    "title_en": rule["title_en"],
                    "severity": rule["severity"],
                    "description_ar": rule["description_ar"],
                    "trigger": trigger_word,
                    "text_excerpt": text[:100],
                    "timestamp": datetime.now().isoformat()
                }
                violations.append(violation)
                self.violations_log.append(violation)

                if rule["severity"] == "critical":
                    self.critical_count += 1
                else:
                    self.warning_count += 1

        return violations

    def get_compliance_score(self) -> Dict:
        """Calculate overall compliance score for the call."""
        total_penalties = (self.critical_count * 20) + (self.warning_count * 5)
        score = max(0, 100 - total_penalties)

        if score >= 90:
            status = {"label_ar": "ممتاز", "label_en": "Excellent", "color": "#4ade80"}
        elif score >= 70:
            status = {"label_ar": "جيد", "label_en": "Good", "color": "#facc15"}
        elif score >= 50:
            status = {"label_ar": "يحتاج تحسين", "label_en": "Needs Improvement", "color": "#fb923c"}
        else:
            status = {"label_ar": "خطير", "label_en": "Critical", "color": "#ef4444"}

        return {
            "score": score,
            "status": status,
            "warnings": self.warning_count,
            "criticals": self.critical_count,
            "total_violations": len(self.violations_log),
            "log": self.violations_log[-5:]  # Last 5 violations
        }

    def reset(self):
        """Reset monitor for a new call."""
        self.violations_log = []
        self.warning_count = 0
        self.critical_count = 0
