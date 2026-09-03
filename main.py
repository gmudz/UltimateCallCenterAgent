"""
AI Sales Copilot — Main FastAPI Server
Real-time AI assistant for financial brokerage call centers.
"""
import os, json, asyncio, shutil
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from engine.client_classifier import classify_client, get_realtime_classification
from engine.objection_handler import detect_objections, get_all_cards
from engine.market_engine import get_market_data, detect_asset_mention, calculate_3m_opportunity, get_trending_assets
from engine.compliance_monitor import ComplianceMonitor
from engine.rag_engine import RAGEngine
from engine.call_simulator import CallSimulator
from engine.suggestion_engine import generate_suggestions
from engine.agent_scorer import AgentScorer
from engine.competitor_engine import detect_competitor, generate_follow_up, get_available_templates
from engine.file_processor import process_uploaded_file, delete_file as delete_training_file, get_uploaded_files, get_categories, UPLOAD_DIR
from engine.auth import authenticate, verify_token, create_user, get_users, delete_user, toggle_user, change_password, COOKIE_NAME
from engine.gemini_engine import generate_response as gemini_generate, save_api_key as gemini_save_key, get_api_key as gemini_get_key, is_configured as gemini_configured
from engine.call_analyzer import analyze_recording, get_recordings, delete_recording, RECORDINGS_DIR, SUPPORTED_AUDIO

# --- App Setup ---
app = FastAPI(title="AI Sales Copilot", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
KB_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.json")

# --- Initialize Engines ---
rag_engine = RAGEngine(knowledge_path=KB_PATH)
call_simulator = CallSimulator()
call_history = []  # In-memory call history

# --- Static Files ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- Auth Helpers ---
def get_current_user(request: Request):
    """Get current user from cookie."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return verify_token(token)

def require_auth(request: Request):
    """Require authentication, redirect to login if not."""
    user = get_current_user(request)
    if not user:
        return None
    return user

def require_admin(request: Request):
    """Require admin role."""
    user = get_current_user(request)
    if not user or user['role'] != 'admin':
        return None
    return user

# --- Page Routes (Protected) ---
@app.get("/login")
async def login_page(request: Request):
    # If already logged in, redirect
    user = get_current_user(request)
    if user:
        return RedirectResponse('/' if user['role'] == 'agent' else '/admin', status_code=302)
    return FileResponse(os.path.join(STATIC_DIR, "login.html"))

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = require_auth(request)
    if not user:
        return RedirectResponse('/login', status_code=302)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# --- REST APIs ---
@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "engines": {
        "rag": rag_engine.get_stats(), "simulator": call_simulator.get_status()
    }}

@app.get("/api/knowledge")
async def knowledge(q: str = ""):
    if q:
        results = rag_engine.search(q, top_k=5)
        return {"query": q, "results": results}
    return {"stats": rag_engine.get_stats()}

@app.get("/api/market-data")
async def market_data():
    return {"instruments": get_market_data(), "trending": get_trending_assets()}

@app.get("/api/scenarios")
async def scenarios():
    return {"scenarios": call_simulator.get_scenarios_list()}

@app.get("/api/battle-cards")
async def battle_cards():
    return {"cards": get_all_cards()}

@app.get("/api/3m/{symbol}")
async def three_m(symbol: str, investment: float = 1000, leverage: int = 100):
    result = calculate_3m_opportunity(symbol.upper(), investment, leverage)
    if result:
        return result
    return {"error": "Symbol not found"}

@app.get("/api/call-history")
async def get_call_history():
    return {"calls": call_history[-20:]}

@app.get("/api/analytics")
async def analytics():
    total_calls = len(call_history)
    if total_calls == 0:
        return {"total_calls": 0, "avg_compliance": 100, "client_types": {}, "objection_types": {}, "avg_duration": 0, "conversion_rate": 0}
    avg_compliance = sum(c.get("compliance_score", 100) for c in call_history) / total_calls
    client_types = {}
    objection_types = {}
    total_duration = 0
    conversions = 0
    for c in call_history:
        ct = c.get("client_type", "unknown")
        client_types[ct] = client_types.get(ct, 0) + 1
        for obj in c.get("objections", []):
            objection_types[obj] = objection_types.get(obj, 0) + 1
        total_duration += c.get("duration_seconds", 0)
        if c.get("converted", False):
            conversions += 1
    return {
        "total_calls": total_calls,
        "avg_compliance": round(avg_compliance, 1),
        "client_types": client_types,
        "objection_types": objection_types,
        "avg_duration": round(total_duration / total_calls, 0) if total_calls else 0,
        "conversion_rate": round(conversions / total_calls * 100, 1) if total_calls else 0
    }

@app.get("/analytics")
async def analytics_page(request: Request):
    if not require_auth(request):
        return RedirectResponse('/login', status_code=302)
    return FileResponse(os.path.join(STATIC_DIR, "analytics.html"))

@app.get("/training")
async def training_page(request: Request):
    if not require_auth(request):
        return RedirectResponse('/login', status_code=302)
    return FileResponse(os.path.join(STATIC_DIR, "training.html"))

@app.get("/admin")
async def admin_page(request: Request):
    if not require_admin(request):
        user = get_current_user(request)
        if not user:
            return RedirectResponse('/login', status_code=302)
        return RedirectResponse('/', status_code=302)
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

@app.get("/users")
async def users_page(request: Request):
    if not require_admin(request):
        user = get_current_user(request)
        if not user:
            return RedirectResponse('/login', status_code=302)
        return RedirectResponse('/', status_code=302)
    return FileResponse(os.path.join(STATIC_DIR, "users.html"))

# --- Auth APIs ---
@app.post("/api/login")
async def api_login(request: Request):
    body = await request.json()
    result = authenticate(body.get('username', ''), body.get('password', ''))
    if not result:
        return JSONResponse({"error": "اسم المستخدم أو كلمة المرور غير صحيحة"}, status_code=401)
    response = JSONResponse({"success": True, "user": result['user']})
    response.set_cookie(
        key=COOKIE_NAME, value=result['token'],
        httponly=True, max_age=86400, samesite='lax'
    )
    return response

@app.post("/api/logout")
async def api_logout():
    response = JSONResponse({"success": True})
    response.delete_cookie(COOKIE_NAME)
    return response

@app.get("/api/me")
async def api_me(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "غير مسجل"}, status_code=401)
    return {"user": user}

@app.get("/api/users")
async def api_list_users(request: Request):
    if not require_admin(request):
        return JSONResponse({"error": "غير مصرح"}, status_code=403)
    return {"users": get_users()}

@app.post("/api/users")
async def api_create_user(request: Request):
    if not require_admin(request):
        return JSONResponse({"error": "غير مصرح"}, status_code=403)
    body = await request.json()
    result = create_user(
        username=body.get('username', ''),
        password=body.get('password', ''),
        display_name=body.get('display_name', ''),
        role=body.get('role', 'agent')
    )
    return result

@app.delete("/api/users/{user_id}")
async def api_delete_user(user_id: int, request: Request):
    if not require_admin(request):
        return JSONResponse({"error": "غير مصرح"}, status_code=403)
    return delete_user(user_id)

@app.post("/api/users/{user_id}/toggle")
async def api_toggle_user(user_id: int, request: Request):
    if not require_admin(request):
        return JSONResponse({"error": "غير مصرح"}, status_code=403)
    return toggle_user(user_id)

@app.get("/api/follow-up")
async def follow_up(template: str = "interested_no_deposit", client_name: str = ""):
    result = generate_follow_up(template, client_name=client_name)
    return result

@app.get("/api/follow-up-templates")
async def follow_up_templates():
    return {"templates": get_available_templates()}

# --- Training File Upload APIs ---
# --- Gemini API Key ---
@app.post("/api/gemini-key")
async def save_gemini_key(request: Request):
    if not require_admin(request):
        return JSONResponse({"error": "غير مصرح"}, status_code=403)
    body = await request.json()
    key = body.get('api_key', '').strip()
    if not key:
        return {"error": "المفتاح فارغ"}
    result = gemini_save_key(key)
    return result

@app.get("/api/gemini-status")
async def gemini_status():
    return {"configured": gemini_configured(), "has_key": bool(gemini_get_key())}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), category: str = Form("auto")):
    """Upload a training file — no size limit, streaming write."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.pdf', '.docx', '.txt', '.json']:
        return {"error": f"نوع الملف غير مدعوم: {ext}"}
    # Stream save — no size limit
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    import uuid
    safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    total_size = 0
    with open(file_path, 'wb') as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            f.write(chunk)
            total_size += len(chunk)
    # Process
    result = process_uploaded_file(
        file_path=file_path,
        original_filename=file.filename,
        category=category,
        rag_engine=rag_engine
    )
    if isinstance(result, dict):
        result['file_size'] = total_size
    return result

@app.get("/api/documents")
async def list_documents():
    """List all uploaded training files."""
    return {"files": get_uploaded_files()}

@app.delete("/api/documents/{file_id}")
async def remove_document(file_id: str):
    """Delete an uploaded file and its documents from the knowledge base."""
    result = delete_training_file(file_id, rag_engine=rag_engine)
    return result

@app.get("/api/categories")
async def list_categories():
    return {"categories": get_categories()}

# --- Call Recording APIs ---
@app.post("/api/upload-recording")
async def upload_recording(file: UploadFile = File(...)):
    """Upload a call recording for transcription and analysis."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_AUDIO:
        return {"error": f"صيغة غير مدعومة: {ext}. المدعوم: {', '.join(SUPPORTED_AUDIO)}"}
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    import uuid
    safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(RECORDINGS_DIR, safe_name)
    with open(file_path, 'wb') as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)
    result = analyze_recording(file_path, file.filename, rag_engine=rag_engine)
    return result

@app.get("/api/recordings")
async def list_recordings():
    return {"recordings": get_recordings()}

@app.delete("/api/recordings/{recording_id}")
async def remove_recording(recording_id: str):
    return delete_recording(recording_id, rag_engine=rag_engine)

# --- WebSocket for Real-time Call Assistance ---
class CallSession:
    def __init__(self):
        self.compliance = ComplianceMonitor()
        self.scorer = AgentScorer()
        self.client_segments: list = []
        self.agent_segments: list = []
        self.all_segments: list = []

    async def process_segment(self, speaker: str, text: str) -> dict:
        self.all_segments.append({"speaker": speaker, "text": text})
        response = {"type": "analysis", "speaker": speaker, "text": text}

        if speaker == "client":
            self.client_segments.append(text)
            classification = classify_client(self.client_segments)
            response["classification"] = classification
            if classification.get("type") != "unknown":
                self._last_client_type = classification["type"]
            objections = detect_objections(text)
            if objections:
                response["objections"] = objections
                if not hasattr(self, '_objection_ids'):
                    self._objection_ids = set()
                for obj in objections:
                    self._objection_ids.add(obj["card"]["id"])
            # Detect asset mentions → 3M opportunities
            assets = detect_asset_mention(text)
            if assets:
                opportunities = []
                for asset in assets[:2]:
                    opp = calculate_3m_opportunity(asset["symbol"])
                    if opp:
                        opportunities.append(opp)
                response["opportunities"] = opportunities
            # RAG context
            context = rag_engine.search(text, top_k=2)
            if context:
                response["rag_results"] = context

        elif speaker == "agent":
            self.agent_segments.append(text)
            # Compliance check
            violations = self.compliance.check_text(text, "agent")
            if violations:
                response["violations"] = violations
            response["compliance_score"] = self.compliance.get_compliance_score()
            # Agent performance scoring
            score_result = self.scorer.score_segment(text)
            response["agent_score"] = score_result

        # Competitor detection
        comp = detect_competitor(text)
        if comp:
            response["competitor"] = comp

        # --- Generate Smart Suggestions ---
        detected_obj_ids = []
        if response.get("objections"):
            detected_obj_ids = [o["card"]["id"] for o in response["objections"]]

        suggestions = generate_suggestions(
            all_segments=self.all_segments,
            client_type=getattr(self, '_last_client_type', 'unknown'),
            latest_text=text,
            speaker=speaker,
            detected_objections=detected_obj_ids,
            rag_engine=rag_engine
        )

        # --- ★ Gemini AI Response ★ ---
        if speaker == "client" and gemini_configured():
            try:
                rag_context = rag_engine.get_context_for_query(text)
                gemini_result = await gemini_generate(
                    client_text=text,
                    rag_context=rag_context,
                    client_type=getattr(self, '_last_client_type', 'unknown'),
                    stage=suggestions.get('stage', {}).get('id', 'presentation'),
                    mood=suggestions.get('mood', {}).get('mood', 'neutral'),
                    conversation_history=self.all_segments
                )
                if gemini_result:
                    suggestions["gemini_response"] = gemini_result
            except Exception as e:
                print(f"Gemini call failed: {e}")

        response["suggestions"] = suggestions

        return response

@app.websocket("/ws/call/{agent_id}")
async def websocket_call(websocket: WebSocket, agent_id: str):
    await websocket.accept()
    session = CallSession()

    async def send_analysis(data):
        """Callback for simulator — process each segment through all engines."""
        if data.get("type") == "transcript":
            analysis = await session.process_segment(data["speaker"], data["text"])
            analysis["segment_index"] = data.get("segment_index", 0)
            analysis["total_segments"] = data.get("total_segments", 0)
            analysis["progress"] = data.get("progress", 0)
            analysis["client_name"] = data.get("client_name", "")
            analysis["is_last"] = data.get("is_last", False)
            await websocket.send_json(analysis)
        elif data.get("type") == "call_ended":
            score = session.compliance.get_compliance_score()
            # Save to call history
            call_record = {
                "client_name": data.get("client_name", ""),
                "compliance_score": score.get("score", 100),
                "total_segments": data.get("total_segments", 0),
                "client_type": getattr(session, '_last_client_type', 'unknown'),
                "objections": list(getattr(session, '_objection_ids', set())),
                "duration_seconds": data.get("total_segments", 0) * 4,
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "converted": False
            }
            call_history.append(call_record)
            # Get agent performance report
            perf_report = session.scorer.get_final_report()
            await websocket.send_json({
                "type": "call_ended",
                "compliance_score": score,
                "total_segments": data.get("total_segments", 0),
                "performance_report": perf_report
            })

    try:
        await websocket.send_json({"type": "connected", "agent_id": agent_id, "scenarios": call_simulator.get_scenarios_list()})
        while True:
            msg = await websocket.receive_json()
            action = msg.get("action")

            if action == "start_demo":
                scenario_id = msg.get("scenario_id", "emotional_client")
                speed = msg.get("speed", 1.0)
                session = CallSession()
                await websocket.send_json({"type": "demo_started", "scenario_id": scenario_id})
                asyncio.create_task(call_simulator.stream_scenario(scenario_id, send_analysis, speed))

            elif action == "stop_demo":
                call_simulator.stop()
                await websocket.send_json({"type": "demo_stopped"})

            elif action == "process_text":
                speaker = msg.get("speaker", "client")
                text = msg.get("text", "")
                analysis = await session.process_segment(speaker, text)
                await websocket.send_json(analysis)

            elif action == "search_knowledge":
                query = msg.get("query", "")
                results = rag_engine.search(query, top_k=5)
                await websocket.send_json({"type": "knowledge_results", "query": query, "results": results})

            elif action == "feedback":
                await websocket.send_json({"type": "feedback_received", "card_id": msg.get("card_id"), "vote": msg.get("vote")})

    except WebSocketDisconnect:
        call_simulator.stop()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
