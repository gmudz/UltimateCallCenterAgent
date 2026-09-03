"""
AI Sales Copilot — Smart Suggestion Engine
Learns from best-employee scripts and provides real-time coaching suggestions.
"""
import json
import os
import re
import random
from typing import Dict, List, Optional

# ---- Load Best Employee Scripts ----
SCRIPTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'best_employee_scripts.json')
SCRIPTS_DATA = {}
try:
    with open(SCRIPTS_PATH, 'r', encoding='utf-8') as f:
        SCRIPTS_DATA = json.load(f)
except Exception as e:
    print(f"Warning: Could not load scripts: {e}")


# ---- Conversation Stage Detection ----
STAGE_PATTERNS = {
    "introduction": {
        "keywords": ["مرحبا", "أهلا", "سلام", "تشرفنا", "كيفك", "كيف حالك", "اسمي", "أنا من"],
        "max_segment": 3  # First 3 segments
    },
    "needs_discovery": {
        "keywords": ["خبرة", "سابق", "تداول قبل", "مبلغ", "ميزانية", "تهتم", "يهمك", "تفضل"],
        "patterns": [r"هل.*سبق", r"كم.*تبدأ", r"وش.*يهم", r"شو.*تبحث"]
    },
    "presentation": {
        "keywords": ["سبريد", "ذهب", "نفط", "أسهم", "منصة", "عقد", "أونصة", "نقطة", "ربح"],
        "patterns": [r"تخيل.*لو", r"السوق.*الحين", r"فرصة.*ممتازة"]
    },
    "objection_handling": {
        "keywords": ["حلال", "حرام", "خسارة", "نصب", "احتيال", "خايف", "أفكر", "مو متأكد"],
        "patterns": [r"مو.*متأكد", r"بفكر.*فيها", r"خايف.*من"]
    },
    "closing": {
        "keywords": ["إيداع", "حساب", "رابط", "واتساب", "هوية", "فتح", "ابدأ", "أبدأ"],
        "patterns": [r"كيف.*أبدأ", r"فتح.*حساب", r"أودع"]
    }
}

# ---- Client Mood Detection ----
MOOD_INDICATORS = {
    "interested": {
        "keywords": ["ممتاز", "حلو", "عجبني", "موافق", "طيب", "تمام", "أكيد", "منيح", "كويس"],
        "patterns": [r"كيف.*أبدأ", r"وش.*أحتاج", r"كم.*أودع", r"أرسل.*رابط"],
        "score": 0.8
    },
    "hesitant": {
        "keywords": ["بفكر", "بشوف", "مو متأكد", "ما أعرف", "يمكن", "بعدين", "مش عارف"],
        "patterns": [r"خلني.*أفكر", r"بعد.*أسبوع", r"مو.*الحين"],
        "score": 0.4
    },
    "resistant": {
        "keywords": ["لا", "ما أبي", "مو مهتم", "خلاص", "بس", "كفاية"],
        "patterns": [r"مو.*مهتم", r"ما.*أبي"],
        "score": 0.2
    },
    "aggressive": {
        "keywords": ["نصب", "احتيال", "كذب", "حرام", "ما أصدق"],
        "patterns": [r"شركت.*نصب", r"كل.*كذب"],
        "score": 0.1
    },
    "silent": {
        "trigger_condition": "no_response",
        "score": 0.3
    }
}


def detect_conversation_stage(segments: List[Dict]) -> str:
    """Detect what stage the conversation is in based on all segments."""
    if len(segments) <= 3:
        return "introduction"

    # Check last 3 segments for stage indicators
    recent_text = " ".join([s.get("text", "") for s in segments[-3:]])
    stage_scores = {}

    for stage, config in STAGE_PATTERNS.items():
        score = 0
        for kw in config.get("keywords", []):
            if kw in recent_text:
                score += 1
        for pat in config.get("patterns", []):
            if re.search(pat, recent_text):
                score += 2
        stage_scores[stage] = score

    # Default progression if no clear signals
    if max(stage_scores.values()) == 0:
        n = len(segments)
        if n <= 3: return "introduction"
        elif n <= 6: return "needs_discovery"
        elif n <= 10: return "presentation"
        else: return "closing"

    return max(stage_scores, key=stage_scores.get)


def detect_client_mood(text: str) -> Dict:
    """Detect the client's current mood from their latest message."""
    best_mood = "neutral"
    best_score = 0.5

    for mood, config in MOOD_INDICATORS.items():
        if mood == "silent":
            continue
        score = 0
        for kw in config.get("keywords", []):
            if kw in text:
                score += 1
        for pat in config.get("patterns", []):
            if re.search(pat, text):
                score += 2
        if score > 0:
            if score > best_score or (score == best_score and config.get("score", 0.5) < best_score):
                best_mood = mood
                best_score = config.get("score", 0.5)

    mood_labels = {
        "interested": {"ar": "مهتم 🟢", "color": "#10b981"},
        "hesitant": {"ar": "متردد 🟡", "color": "#f59e0b"},
        "resistant": {"ar": "رافض 🔴", "color": "#ef4444"},
        "aggressive": {"ar": "عدواني ⛔", "color": "#dc2626"},
        "neutral": {"ar": "محايد ⚪", "color": "#94a3b8"}
    }
    label = mood_labels.get(best_mood, mood_labels["neutral"])
    return {"mood": best_mood, "label_ar": label["ar"], "color": label["color"], "engagement_score": best_score}


def get_stage_suggestions(stage: str, client_type: str = None) -> List[Dict]:
    """Get best-practice suggestions for the current conversation stage."""
    stage_data = SCRIPTS_DATA.get("conversation_stages", {}).get(stage, {})
    if not stage_data:
        return []

    suggestions = []
    # Best practices
    for practice in stage_data.get("best_practices", []):
        suggestions.append({
            "type": "best_practice",
            "icon": "💡",
            "text": practice,
            "category_ar": "أفضل الممارسات"
        })

    # Suggested phrases
    phrases = stage_data.get("suggested_phrases", [])
    if phrases:
        selected = random.sample(phrases, min(2, len(phrases)))
        for phrase in selected:
            suggestions.append({
                "type": "suggested_phrase",
                "icon": "💬",
                "text": phrase,
                "category_ar": "جملة مقترحة",
                "copyable": True
            })

    return suggestions


def get_closing_suggestions(client_type: str) -> List[Dict]:
    """Get closing technique based on client personality type."""
    techniques = SCRIPTS_DATA.get("closing_techniques", [])
    suggestions = []

    for tech in techniques:
        if client_type in tech.get("client_types", []):
            scripts = tech.get("scripts", [])
            selected_script = random.choice(scripts) if scripts else ""
            suggestions.append({
                "type": "closing_technique",
                "icon": "🎯",
                "title_ar": tech["name_ar"],
                "text": selected_script,
                "description": tech.get("when_to_use", ""),
                "category_ar": "تقنية إغلاق",
                "copyable": True
            })

    return suggestions[:2]  # Max 2 closing suggestions


def get_situational_suggestion(client_text: str, agent_text: str = None) -> Optional[Dict]:
    """Detect special situations and provide matching suggestions."""
    situations = SCRIPTS_DATA.get("situational_suggestions", {})

    # Check for money mention
    money_patterns = [r'\d+\s*دولار', r'\$\d+', r'\d+\s*ريال', r'\d+\s*دينار', r'مبلغ', r'ميزانية']
    for pat in money_patterns:
        if re.search(pat, client_text):
            sit = situations.get("client_mentions_money", {})
            if sit:
                return {
                    "type": "situational",
                    "icon": "💰",
                    "title_ar": "💰 العميل ذكر مبلغ!",
                    "suggestions": sit.get("suggestions", []),
                    "category_ar": "اقتراح لحظي",
                    "priority": "high"
                }

    # Check interest signals
    interest_kw = ["كيف أبدأ", "أبي أبدأ", "أرسل الرابط", "شلون أودع", "كم أودع"]
    for kw in interest_kw:
        if kw in client_text:
            sit = situations.get("client_interested", {})
            if sit:
                return {
                    "type": "situational",
                    "icon": "🎯",
                    "title_ar": "🎯 العميل مهتم — أغلق الآن!",
                    "suggestions": sit.get("suggestions", []),
                    "category_ar": "فرصة إغلاق",
                    "priority": "critical"
                }

    # Check hesitation
    hesitant_kw = ["بفكر", "بشوف", "مو متأكد", "خلني أفكر", "بعدين", "مش عارف", "يمكن"]
    for kw in hesitant_kw:
        if kw in client_text:
            sit = situations.get("client_hesitant", {})
            if sit:
                return {
                    "type": "situational",
                    "icon": "⏰",
                    "title_ar": "⏰ العميل متردد — استخدم هذه التقنيات",
                    "suggestions": sit.get("suggestions", []),
                    "category_ar": "تقنية تحويل",
                    "priority": "high"
                }

    # Check aggression
    aggressive_kw = ["نصب", "احتيال", "كذب", "ما أصدق"]
    for kw in aggressive_kw:
        if kw in client_text:
            sit = situations.get("client_aggressive", {})
            if sit:
                return {
                    "type": "situational",
                    "icon": "🛡️",
                    "title_ar": "🛡️ العميل عدواني — هدّئ الموقف",
                    "suggestions": sit.get("suggestions", []),
                    "category_ar": "إدارة الموقف",
                    "priority": "high"
                }

    return None


def get_objection_script(objection_id: str) -> Optional[Dict]:
    """Get the best-employee response script for a specific objection."""
    responses = SCRIPTS_DATA.get("objection_responses", {})
    response = responses.get(objection_id)
    if not response:
        return None

    return {
        "type": "objection_script",
        "icon": "📝",
        "title_ar": f"📝 سكربت أفضل موظف — {objection_id}",
        "script": response["best_employee_script"],
        "key_points": response.get("key_points", []),
        "tone": response.get("tone", ""),
        "category_ar": "رد أفضل موظف",
        "copyable": True,
        "priority": "critical"
    }


def generate_suggestions(
    all_segments: List[Dict],
    client_type: str = "unknown",
    latest_text: str = "",
    speaker: str = "client",
    detected_objections: List[str] = None,
    rag_engine=None
) -> Dict:
    """
    Main function: Generate real-time suggestions based on full conversation context.
    Now enhanced with RAG-powered answers from uploaded training files.
    """
    result = {
        "stage": {},
        "mood": {},
        "suggestions": [],
        "closing": [],
        "situational": None,
        "objection_script": None,
        "rag_answers": []
    }

    # 1. Detect conversation stage
    stage = detect_conversation_stage(all_segments)
    stage_data = SCRIPTS_DATA.get("conversation_stages", {}).get(stage, {})
    result["stage"] = {
        "id": stage,
        "name_ar": {
            "introduction": "مرحلة التعارف",
            "needs_discovery": "اكتشاف الاحتياجات",
            "presentation": "العرض والتقديم",
            "objection_handling": "معالجة الاعتراضات",
            "closing": "مرحلة الإغلاق"
        }.get(stage, stage),
        "goal": stage_data.get("goal", ""),
        "icon": {"introduction":"👋","needs_discovery":"🔍","presentation":"📊","objection_handling":"⚔️","closing":"🎯"}.get(stage, "📋")
    }

    # 2. Detect client mood (only from client messages)
    if speaker == "client" and latest_text:
        result["mood"] = detect_client_mood(latest_text)

    # 3. Stage-specific best practices
    stage_tips = get_stage_suggestions(stage, client_type)
    result["suggestions"].extend(stage_tips[:3])

    # 4. Closing techniques if in closing stage or client showing interest
    if stage in ("closing", "presentation") and client_type != "unknown":
        closings = get_closing_suggestions(client_type)
        result["closing"] = closings

    # 5. Situational suggestions based on latest client text
    if speaker == "client" and latest_text:
        situational = get_situational_suggestion(latest_text)
        if situational:
            result["situational"] = situational

    # 6. Objection-specific best-employee scripts
    if detected_objections:
        for obj_id in detected_objections[:1]:
            script = get_objection_script(obj_id)
            if script:
                result["objection_script"] = script

    # 7. ★ RAG-Powered Suggestions from uploaded training files ★
    if rag_engine and latest_text and len(latest_text) > 5:
        rag_answers = []

        # A. Search for direct answer to what the client said
        if speaker == "client":
            rag_results = rag_engine.search(latest_text, top_k=3)
            for r in rag_results:
                doc = r.get("document", {})
                text_content = doc.get("text", "")
                meta = doc.get("metadata", {})
                score = r.get("score", 0)
                if score > 0.1 and len(text_content) > 20:
                    source_name = meta.get("source_name", "قاعدة المعرفة")
                    doc_type = meta.get("type", "general")
                    type_icons = {
                        "scripts": "📝", "objections": "⚔️",
                        "company_info": "📋", "terms": "📖",
                        "competitors": "🏢", "general": "📄"
                    }
                    type_labels = {
                        "scripts": "سكربت", "objections": "رد على اعتراض",
                        "company_info": "معلومات الشركة", "terms": "مصطلحات",
                        "competitors": "منافسين", "general": "معلومات"
                    }
                    rag_answers.append({
                        "type": "rag_answer",
                        "icon": type_icons.get(doc_type, "📄"),
                        "title_ar": f"💡 {type_labels.get(doc_type, 'معلومات')} — من {source_name}",
                        "text": text_content,
                        "source": source_name,
                        "category": doc_type,
                        "category_ar": type_labels.get(doc_type, "معلومات"),
                        "copyable": True,
                        "priority": "high" if doc_type in ("scripts", "objections") else "normal",
                        "score": round(score, 2)
                    })

        # B. Specific objection answers from training files
        if detected_objections and speaker == "client":
            for obj_id in detected_objections[:2]:
                # Search RAG specifically for this objection
                obj_query = f"رد على اعتراض {obj_id} حل معارضة"
                obj_results = rag_engine.search(obj_query, top_k=2)
                for r in obj_results:
                    doc = r.get("document", {})
                    text_content = doc.get("text", "")
                    meta = doc.get("metadata", {})
                    if len(text_content) > 20:
                        source_name = meta.get("source_name", "ملف التدريب")
                        rag_answers.append({
                            "type": "rag_objection_answer",
                            "icon": "⚡",
                            "title_ar": f"⚡ حل المعارضة — من {source_name}",
                            "text": text_content,
                            "source": source_name,
                            "copyable": True,
                            "priority": "critical",
                            "objection_id": obj_id
                        })

        # Deduplicate and limit
        seen_texts = set()
        unique_answers = []
        for a in rag_answers:
            short = a["text"][:80]
            if short not in seen_texts:
                seen_texts.add(short)
                unique_answers.append(a)
        result["rag_answers"] = unique_answers[:5]

    return result

