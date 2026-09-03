"""
AI Sales Copilot — File Processor Engine
Processes uploaded training files (PDF, DOCX, TXT, JSON) into RAG knowledge base.
"""
import os
import json
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
MANIFEST_PATH = os.path.join(UPLOAD_DIR, '_manifest.json')

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Category labels
CATEGORIES = {
    "company_info": {"ar": "معلومات الشركة", "icon": "📋"},
    "scripts": {"ar": "سكربتات المبيعات", "icon": "📝"},
    "objections": {"ar": "معارضات وحلولها", "icon": "⚔️"},
    "terms": {"ar": "مصطلحات ومعلومات", "icon": "📖"},
    "competitors": {"ar": "بيانات المنافسين", "icon": "🏢"},
    "general": {"ar": "عام", "icon": "📄"}
}


def get_manifest() -> List[Dict]:
    """Load the upload manifest."""
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_manifest(manifest: List[Dict]):
    """Save the upload manifest."""
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    if not HAS_PYPDF2:
        return ""
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    if not HAS_DOCX:
        return ""
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return text.strip()


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a TXT file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def extract_text_from_json(file_path: str) -> str:
    """Extract text from a JSON file — flatten all string values."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    texts = []
    def flatten(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                flatten(v, f"{prefix}{k}: ")
        elif isinstance(obj, list):
            for item in obj:
                flatten(item, prefix)
        elif isinstance(obj, str) and len(obj) > 10:
            texts.append(prefix + obj)
    flatten(data)
    return "\n".join(texts)


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Split text into chunks of approximately chunk_size words."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0

    for word in words:
        current_chunk.append(word)
        current_size += 1
        if current_size >= chunk_size:
            # Try to break at sentence boundary
            chunk_text_str = ' '.join(current_chunk)
            last_period = max(
                chunk_text_str.rfind('.'),
                chunk_text_str.rfind('。'),
                chunk_text_str.rfind('؟'),
                chunk_text_str.rfind('!')
            )
            if last_period > len(chunk_text_str) * 0.5:
                chunks.append(chunk_text_str[:last_period + 1].strip())
                remaining = chunk_text_str[last_period + 1:].strip()
                current_chunk = remaining.split() if remaining else []
                current_size = len(current_chunk)
            else:
                chunks.append(chunk_text_str)
                current_chunk = []
                current_size = 0

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return [c for c in chunks if len(c.strip()) > 20]


def auto_detect_category(text: str) -> str:
    """Auto-detect the category of a text chunk."""
    lower = text.lower()
    # Objections
    objection_kw = ['اعتراض', 'معارضة', 'رد على', 'الرد على', 'حلال', 'حرام', 'نصب', 'خسارة', 'منافس']
    if any(kw in lower for kw in objection_kw):
        return 'objections'
    # Scripts
    script_kw = ['سكربت', 'افتتاح', 'إغلاق', 'عبارة', 'قل للعميل', 'الرد المقترح']
    if any(kw in lower for kw in script_kw):
        return 'scripts'
    # Company info
    company_kw = ['ترخيص', 'شركة', 'إيفست', 'evest', 'خدمات', 'مميزات', 'عن ال']
    if any(kw in lower for kw in company_kw):
        return 'company_info'
    # Competitors
    comp_kw = ['منافس', 'مقارنة', 'exness', 'xtb', 'etoro', 'ic markets']
    if any(kw in lower for kw in comp_kw):
        return 'competitors'
    # Terms
    terms_kw = ['مصطلح', 'تعريف', 'سبريد', 'رافعة', 'هامش', 'pip', 'lot']
    if any(kw in lower for kw in terms_kw):
        return 'terms'
    return 'general'


def process_uploaded_file(
    file_path: str,
    original_filename: str,
    category: str = "auto",
    rag_engine=None
) -> Dict:
    """Process an uploaded file and add it to the RAG knowledge base."""
    ext = os.path.splitext(original_filename)[1].lower()

    # Extract text based on file type
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif ext == '.docx':
        text = extract_text_from_docx(file_path)
    elif ext == '.txt':
        text = extract_text_from_txt(file_path)
    elif ext == '.json':
        text = extract_text_from_json(file_path)
    else:
        return {"error": f"Unsupported file type: {ext}"}

    if not text or len(text.strip()) < 20:
        return {"error": "الملف فارغ أو لا يحتوي على نص كافٍ"}

    # Generate unique ID
    file_id = str(uuid.uuid4())[:8]

    # Chunk the text
    chunks = chunk_text(text, chunk_size=400)

    # Auto-detect or use provided category
    if category == "auto":
        category = auto_detect_category(text[:1000])

    # Add chunks to RAG engine
    docs_added = 0
    if rag_engine:
        for i, chunk in enumerate(chunks):
            rag_engine.add_document(
                text=chunk,
                metadata={
                    "type": category,
                    "source_file": file_id,
                    "source_name": original_filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            docs_added += 1
        rag_engine._build_index()

    # ★ Deep analysis with Gemini ★
    extracted = {"qa_pairs": 0, "objections": 0, "techniques": 0}
    try:
        extracted = _deep_analyze_with_gemini(text, file_id, original_filename, rag_engine, file_path=file_path)
    except Exception as e:
        print(f"Deep analysis skipped: {e}")

    # Save to manifest
    manifest = get_manifest()
    record = {
        "id": file_id,
        "filename": original_filename,
        "category": category,
        "category_ar": CATEGORIES.get(category, CATEGORIES["general"])["ar"],
        "icon": CATEGORIES.get(category, CATEGORIES["general"])["icon"],
        "file_type": ext,
        "text_length": len(text),
        "chunks": len(chunks),
        "docs_added": docs_added,
        "extracted": extracted,
        "uploaded_at": datetime.now().isoformat(),
        "file_path": file_path
    }
    manifest.append(record)
    save_manifest(manifest)

    return {
        "success": True,
        "file_id": file_id,
        "filename": original_filename,
        "category": category,
        "category_ar": CATEGORIES.get(category, CATEGORIES["general"])["ar"],
        "chunks_created": len(chunks),
        "text_length": len(text),
        "docs_added": docs_added,
        "extracted": extracted
    }


def _deep_analyze_with_gemini(text: str, file_id: str, filename: str, rag_engine, file_path: str = None) -> Dict:
    """
    Use Gemini to deeply analyze uploaded files.
    For PDFs: uploads the file directly to Gemini Files API for native reading.
    For other formats: sends extracted text.
    """
    from engine.gemini_engine import get_api_key
    api_key = get_api_key()
    if not api_key or not rag_engine:
        return {"qa_pairs": 0, "objections": 0, "techniques": 0}

    from google import genai
    client = genai.Client(api_key=api_key)

    ext = os.path.splitext(filename)[1].lower()

    # ★ For PDFs: upload directly to Gemini for native reading ★
    uploaded_file = None
    if ext == '.pdf' and file_path and os.path.exists(file_path):
        try:
            uploaded_file = client.files.upload(file=file_path)
        except Exception as e:
            print(f"PDF upload to Gemini failed: {e}")

    analysis_prompt = """حلّل هذا المستند بدقة شديدة واستخرج منه **كل** المعلومات التالية بصيغة JSON.
هذا ملف تدريب لموظفي مبيعات — استخرج كل ما يمكن أن يفيد الموظف في الرد على العملاء.

المطلوب:

1. "qa_pairs": استخرج **كل** سؤال ممكن أن يسأله عميل وجوابه من المستند.
   - ابحث عن أسئلة صريحة وأيضاً استنتج أسئلة من المعلومات الموجودة.
   - مثال: إذا المستند يذكر "الشركة مرخصة من CySEC" → أضف سؤال "هل الشركة مرخصة؟"
   - كل عنصر: {"q": "السؤال الكامل", "a": "الجواب المفصّل والكامل كما ورد في المستند"}

2. "objections": استخرج **كل** معارضة أو اعتراض ممكن وحلّه.
   - ابحث عن: اعتراضات صريحة، مخاوف، شكوك، أسباب رفض
   - إذا المستند يذكر مميزة → استنتج المعارضة المقابلة
   - مثال: "حساب إسلامي بدون فوائد" → معارضة "هل التداول حلال؟"
   - كل عنصر: {"objection": "المعارضة/الاعتراض", "solution": "الحل/الرد الكامل والمقنع"}

3. "techniques": استخرج تقنيات البيع وفن الإقناع والحوار.
   - كل عنصر: {"name": "اسم التقنية", "description": "الشرح المفصّل", "example": "مثال عملي من المستند"}

4. "product_info": استخرج **كل** معلومة عن المنتج/الخدمة/الشركة.
   - التراخيص، المميزات، الأرقام، الخدمات، المنصات، الحسابات، العروض
   - كل عنصر: {"topic": "الموضوع", "info": "المعلومات الكاملة"}

5. "full_text": النص الكامل المستخرج من المستند (أول 10000 حرف)

## مهم جداً:
- كن شاملاً — استخرج أكبر عدد ممكن من العناصر
- الأجوبة يجب أن تكون كاملة ومفصّلة كما وردت في المستند
- إذا المستند يحتوي جداول أو أرقام → ضمّنها في الأجوبة
- أعد JSON صالح فقط بدون أي نص إضافي"""

    try:
        # Build content based on file type
        if uploaded_file:
            # PDF: send file directly to Gemini
            contents = [uploaded_file, analysis_prompt]
        else:
            # Other formats: send text
            analysis_text = text[:15000]
            contents = f"{analysis_prompt}\n\nالنص:\n\"\"\"\n{analysis_text}\n\"\"\""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config={"temperature": 0.1, "max_output_tokens": 8000}
        )

        response_text = response.text.strip() if response.text else ""
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)

        data = json.loads(response_text)
        counts = {"qa_pairs": 0, "objections": 0, "techniques": 0}

        # ★ If Gemini extracted better text from PDF, use it for RAG chunks ★
        gemini_text = data.get("full_text", "")
        if gemini_text and len(gemini_text) > len(text) * 0.5 and ext == '.pdf':
            better_chunks = chunk_text(gemini_text, chunk_size=400)
            # Remove old chunks and add better ones
            rag_engine.remove_documents_by_source(file_id)
            for i, chunk in enumerate(better_chunks):
                rag_engine.add_document(
                    text=chunk,
                    metadata={
                        "type": "product_info",
                        "source_file": file_id,
                        "source_name": filename,
                        "chunk_index": i,
                        "total_chunks": len(better_chunks)
                    }
                )
            print(f"Replaced PDF chunks: {len(better_chunks)} (Gemini-extracted text)")


        # Add extracted Q&A pairs to RAG
        for qa in data.get("qa_pairs", []):
            q = qa.get("q", "")
            a = qa.get("a", "")
            if q and a and len(a) > 10:
                rag_engine.add_document(
                    text=f"سؤال: {q}\nالجواب: {a}",
                    metadata={"type": "qa_pair", "source_file": file_id, "source_name": filename, "question": q}
                )
                counts["qa_pairs"] += 1

        # Add extracted objections to RAG
        for obj in data.get("objections", []):
            objection = obj.get("objection", "")
            solution = obj.get("solution", "")
            if objection and solution and len(solution) > 10:
                rag_engine.add_document(
                    text=f"معارضة العميل: {objection}\nالرد الصحيح: {solution}",
                    metadata={"type": "objection_solution", "source_file": file_id, "source_name": filename, "objection": objection}
                )
                counts["objections"] += 1

        # Add sales techniques to RAG
        for tech in data.get("techniques", []):
            name = tech.get("name", "")
            desc = tech.get("description", "")
            example = tech.get("example", "")
            if name and desc:
                text_entry = f"تقنية بيع: {name}\n{desc}"
                if example:
                    text_entry += f"\nمثال: {example}"
                rag_engine.add_document(
                    text=text_entry,
                    metadata={"type": "sales_technique", "source_file": file_id, "source_name": filename}
                )
                counts["techniques"] += 1

        # Add product info to RAG
        for info in data.get("product_info", []):
            topic = info.get("topic", "")
            info_text = info.get("info", "")
            if topic and info_text:
                rag_engine.add_document(
                    text=f"{topic}: {info_text}",
                    metadata={"type": "product_info", "source_file": file_id, "source_name": filename}
                )

        if counts["qa_pairs"] + counts["objections"] + counts["techniques"] > 0:
            rag_engine._build_index()

        return counts

    except Exception as e:
        print(f"Deep analysis error: {e}")
        return {"qa_pairs": 0, "objections": 0, "techniques": 0}


def delete_file(file_id: str, rag_engine=None) -> Dict:
    """Delete an uploaded file and remove its documents from RAG."""
    manifest = get_manifest()
    record = next((r for r in manifest if r["id"] == file_id), None)
    if not record:
        return {"error": "File not found"}

    # Remove from RAG
    if rag_engine:
        rag_engine.remove_documents_by_source(file_id)

    # Remove physical file
    if os.path.exists(record.get("file_path", "")):
        os.remove(record["file_path"])

    # Update manifest
    manifest = [r for r in manifest if r["id"] != file_id]
    save_manifest(manifest)

    return {"success": True, "deleted_id": file_id, "filename": record["filename"]}


def get_uploaded_files() -> List[Dict]:
    """Get list of uploaded files."""
    manifest = get_manifest()
    return [{
        "id": r["id"],
        "filename": r["filename"],
        "category": r["category"],
        "category_ar": r.get("category_ar", r["category"]),
        "icon": r.get("icon", "📄"),
        "file_type": r["file_type"],
        "chunks": r["chunks"],
        "uploaded_at": r["uploaded_at"]
    } for r in manifest]


def get_categories() -> List[Dict]:
    """Get available categories."""
    return [{"id": k, "ar": v["ar"], "icon": v["icon"]} for k, v in CATEGORIES.items()]
