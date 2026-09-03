"""
AI Sales Copilot — Call Recording Analyzer
Transcribes and analyzes audio recordings using Gemini.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Optional


RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'recordings')
RECORDINGS_MANIFEST = os.path.join(RECORDINGS_DIR, '_manifest.json')
os.makedirs(RECORDINGS_DIR, exist_ok=True)

SUPPORTED_AUDIO = ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.flac']


def get_recordings_manifest():
    if os.path.exists(RECORDINGS_MANIFEST):
        with open(RECORDINGS_MANIFEST, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_recordings_manifest(manifest):
    with open(RECORDINGS_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def analyze_recording(file_path: str, original_filename: str, rag_engine=None) -> Dict:
    """
    Transcribe and analyze a call recording using Gemini.
    Extracts: transcript, strengths, weaknesses, objection handling examples, techniques.
    """
    from engine.gemini_engine import get_api_key
    api_key = get_api_key()
    if not api_key:
        return {"error": "Gemini غير مفعّل — أدخل مفتاح API أولاً"}

    recording_id = str(uuid.uuid4())[:8]

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        # Upload the audio file to Gemini
        uploaded_file = client.files.upload(file=file_path)

        # Step 1: Transcribe the audio
        transcription_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                uploaded_file,
                """فرّغ هذا التسجيل الصوتي بالكامل لمكالمة بيع.
حدد المتحدث (موظف/عميل) لكل جزء.
اكتب النص بصيغة:
موظف: ...
عميل: ...

فرّغ كل ما يُقال بدقة بالعربية."""
            ],
            config={"temperature": 0.1, "max_output_tokens": 4000}
        )
        transcript = transcription_response.text.strip() if transcription_response.text else ""

        if not transcript or len(transcript) < 30:
            return {"error": "لم يتم التعرف على كلام في التسجيل"}

        # Step 2: Deep analysis of the call
        analysis_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""حلّل مكالمة المبيع التالية وأعد JSON يحتوي:

1. "summary": ملخص المكالمة (2-3 جمل)
2. "strengths": قائمة نقاط القوة للموظف (كل عنصر نص)
3. "weaknesses": قائمة نقاط الضعف والأخطاء (كل عنصر نص)
4. "objection_handling": قائمة المعارضات وكيف تعامل معها الموظف. كل عنصر: {{"objection": "المعارضة", "response": "رد الموظف", "was_effective": true/false, "better_response": "رد أفضل مقترح"}}
5. "techniques_used": قائمة تقنيات البيع المستخدمة: {{"name": "التقنية", "example": "مثال من المكالمة", "effectiveness": "عالية/متوسطة/منخفضة"}}
6. "qa_extracted": قائمة أسئلة العميل وأجوبة الموظف: {{"q": "السؤال", "a": "الجواب"}}
7. "score": تقييم الموظف من 10
8. "advice": نصيحة واحدة مهمة للتحسين

أعد JSON فقط بدون نص إضافي.

المكالمة:
\"\"\"
{transcript}
\"\"\" """,
            config={"temperature": 0.2, "max_output_tokens": 4000}
        )

        import re
        analysis_text = analysis_response.text.strip() if analysis_response.text else "{}"
        if analysis_text.startswith("```"):
            analysis_text = re.sub(r'^```(?:json)?\s*', '', analysis_text)
            analysis_text = re.sub(r'\s*```$', '', analysis_text)

        analysis = json.loads(analysis_text)

        # Step 3: Add extracted knowledge to RAG
        docs_added = 0
        if rag_engine:
            # Add full transcript
            rag_engine.add_document(
                text=f"تفريغ مكالمة: {transcript[:2000]}",
                metadata={"type": "call_transcript", "source_file": recording_id, "source_name": original_filename}
            )
            docs_added += 1

            # Add effective objection handling
            for obj in analysis.get("objection_handling", []):
                response_text = obj.get("better_response", obj.get("response", ""))
                objection_text = obj.get("objection", "")
                if objection_text and response_text:
                    rag_engine.add_document(
                        text=f"معارضة العميل: {objection_text}\nالرد الصحيح: {response_text}",
                        metadata={
                            "type": "objection_solution",
                            "source_file": recording_id,
                            "source_name": f"تسجيل: {original_filename}",
                            "was_effective": obj.get("was_effective", False)
                        }
                    )
                    docs_added += 1

            # Add Q&A pairs
            for qa in analysis.get("qa_extracted", []):
                q = qa.get("q", "")
                a = qa.get("a", "")
                if q and a:
                    rag_engine.add_document(
                        text=f"سؤال: {q}\nالجواب: {a}",
                        metadata={"type": "qa_pair", "source_file": recording_id, "source_name": f"تسجيل: {original_filename}"}
                    )
                    docs_added += 1

            # Add effective techniques as learning material
            for tech in analysis.get("techniques_used", []):
                if tech.get("effectiveness") in ("عالية", "متوسطة"):
                    rag_engine.add_document(
                        text=f"تقنية بيع ناجحة: {tech['name']}\nمثال عملي: {tech.get('example', '')}",
                        metadata={"type": "sales_technique", "source_file": recording_id, "source_name": f"تسجيل: {original_filename}"}
                    )
                    docs_added += 1

            if docs_added > 0:
                rag_engine._build_index()

        # Save to manifest
        manifest = get_recordings_manifest()
        record = {
            "id": recording_id,
            "filename": original_filename,
            "file_path": file_path,
            "transcript_length": len(transcript),
            "score": analysis.get("score", 0),
            "summary": analysis.get("summary", ""),
            "strengths_count": len(analysis.get("strengths", [])),
            "weaknesses_count": len(analysis.get("weaknesses", [])),
            "objections_count": len(analysis.get("objection_handling", [])),
            "docs_added": docs_added,
            "uploaded_at": datetime.now().isoformat()
        }
        manifest.append(record)
        save_recordings_manifest(manifest)

        return {
            "success": True,
            "recording_id": recording_id,
            "filename": original_filename,
            "transcript": transcript,
            "analysis": analysis,
            "docs_added": docs_added
        }

    except Exception as e:
        print(f"Recording analysis error: {e}")
        return {"error": f"خطأ في تحليل التسجيل: {str(e)}"}


def get_recordings() -> list:
    return get_recordings_manifest()


def delete_recording(recording_id: str, rag_engine=None) -> Dict:
    manifest = get_recordings_manifest()
    record = next((r for r in manifest if r["id"] == recording_id), None)
    if not record:
        return {"error": "التسجيل غير موجود"}
    if rag_engine:
        rag_engine.remove_documents_by_source(recording_id)
    if os.path.exists(record.get("file_path", "")):
        os.remove(record["file_path"])
    manifest = [r for r in manifest if r["id"] != recording_id]
    save_recordings_manifest(manifest)
    return {"success": True, "deleted_id": recording_id}
