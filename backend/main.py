import os
import json
import base64
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import websockets
from dotenv import load_dotenv

from database import init_db, get_db, SessionLocal, User, Conversation, Message
from functions import execute_function
from prompts import SYSTEM_PROMPT, TOOLS

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2025-06-03"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    # Create a default user if none exists
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            user = User(name="Runner")
            db.add(user)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="Stride - Voice Running Coach", lifespan=lifespan)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ REST API Endpoints ============

@app.get("/")
async def root():
    return {"message": "Stride - Voice Running Coach API", "status": "running"}


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "name": user.name}
    finally:
        db.close()


@app.get("/api/users/{user_id}/conversations")
async def get_conversations(user_id: int):
    db = SessionLocal()
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.created_at.desc()).all()
        
        return [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "message_count": len(c.messages)
            }
            for c in conversations
        ]
    finally:
        db.close()


@app.post("/api/users/{user_id}/conversations")
async def create_conversation(user_id: int):
    db = SessionLocal()
    try:
        conversation = Conversation(user_id=user_id, title="New Conversation")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return {"id": conversation.id, "title": conversation.title}
    finally:
        db.close()


@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: int):
    db = SessionLocal()
    try:
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    finally:
        db.close()


@app.get("/api/users/{user_id}/runs")
async def get_runs(user_id: int, limit: int = 20):
    db = SessionLocal()
    try:
        from database import Run
        runs = db.query(Run).filter(
            Run.user_id == user_id
        ).order_by(Run.run_date.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "distance_miles": r.distance_miles,
                "duration_minutes": r.duration_minutes,
                "pace_per_mile": r.pace_per_mile,
                "notes": r.notes,
                "run_date": r.run_date.isoformat()
            }
            for r in runs
        ]
    finally:
        db.close()


@app.get("/api/users/{user_id}/goals")
async def get_user_goals(user_id: int):
    db = SessionLocal()
    try:
        from database import Goal
        from datetime import date
        goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.race_date >= date.today()
        ).order_by(Goal.race_date).all()
        
        return [
            {
                "id": g.id,
                "race_name": g.race_name,
                "race_date": g.race_date.isoformat(),
                "target_time": g.target_time,
                "distance_miles": g.distance_miles
            }
            for g in goals
        ]
    finally:
        db.close()


# ============ WebSocket for Voice Chat ============

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time voice chat."""
    await websocket.accept()
    
    db = SessionLocal()
    
    try:
        # Create or get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, name="Runner")
            db.add(user)
            db.commit()
        
        # Create a new conversation
        conversation = Conversation(user_id=user_id, title="Voice Chat")
        db.add(conversation)
        db.commit()
        conversation_id = conversation.id
        
        # Connect to OpenAI Realtime API
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        async with websockets.connect(OPENAI_REALTIME_URL, extra_headers=headers) as openai_ws:
            
            # Configure the session
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": SYSTEM_PROMPT,
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    },
                    "tools": TOOLS,
                    "tool_choice": "auto"
                }
            }
            
            await openai_ws.send(json.dumps(session_config))
            
            async def receive_from_client():
                """Receive audio from frontend and forward to OpenAI."""
                try:
                    while True:
                        data = await websocket.receive()
                        
                        if "bytes" in data:
                            # Audio data - forward to OpenAI
                            audio_base64 = base64.b64encode(data["bytes"]).decode()
                            audio_event = {
                                "type": "input_audio_buffer.append",
                                "audio": audio_base64
                            }
                            await openai_ws.send(json.dumps(audio_event))
                        
                        elif "text" in data:
                            # Text command from frontend
                            msg = json.loads(data["text"])
                            
                            if msg.get("type") == "commit_audio":
                                await openai_ws.send(json.dumps({
                                    "type": "input_audio_buffer.commit"
                                }))
                            
                            elif msg.get("type") == "text_message":
                                # Send text message
                                await openai_ws.send(json.dumps({
                                    "type": "conversation.item.create",
                                    "item": {
                                        "type": "message",
                                        "role": "user",
                                        "content": [
                                            {"type": "input_text", "text": msg["text"]}
                                        ]
                                    }
                                }))
                                await openai_ws.send(json.dumps({"type": "response.create"}))
                
                except WebSocketDisconnect:
                    pass
            
            async def receive_from_openai():
                """Receive from OpenAI and forward to frontend."""
                try:
                    async for message in openai_ws:
                        event = json.loads(message)
                        event_type = event.get("type", "")
                        
                        # Forward audio to client
                        if event_type == "response.audio.delta":
                            audio_data = base64.b64decode(event["delta"])
                            await websocket.send_bytes(audio_data)
                        
                        # Forward transcripts
                        elif event_type == "conversation.item.input_audio_transcription.completed":
                            transcript = event.get("transcript", "")
                            if transcript:
                                # Save user message to database
                                msg = Message(
                                    conversation_id=conversation_id,
                                    role="user",
                                    content=transcript
                                )
                                db.add(msg)
                                db.commit()
                                
                                await websocket.send_text(json.dumps({
                                    "type": "user_transcript",
                                    "text": transcript
                                }))
                        
                        elif event_type == "response.audio_transcript.delta":
                            await websocket.send_text(json.dumps({
                                "type": "assistant_transcript_delta",
                                "text": event.get("delta", "")
                            }))
                        
                        elif event_type == "response.audio_transcript.done":
                            transcript = event.get("transcript", "")
                            if transcript:
                                # Save assistant message to database
                                msg = Message(
                                    conversation_id=conversation_id,
                                    role="assistant",
                                    content=transcript
                                )
                                db.add(msg)
                                db.commit()
                                
                                await websocket.send_text(json.dumps({
                                    "type": "assistant_transcript",
                                    "text": transcript
                                }))
                        
                        # Handle function calls
                        elif event_type == "response.function_call_arguments.done":
                            function_name = event.get("name")
                            arguments = json.loads(event.get("arguments", "{}"))
                            call_id = event.get("call_id")
                            
                            # Execute the function
                            result = await execute_function(db, user_id, function_name, arguments)
                            
                            # Send result back to OpenAI
                            await openai_ws.send(json.dumps({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": json.dumps(result)
                                }
                            }))
                            
                            # Trigger response generation
                            await openai_ws.send(json.dumps({"type": "response.create"}))
                            
                            # Notify frontend about function call
                            await websocket.send_text(json.dumps({
                                "type": "function_call",
                                "name": function_name,
                                "arguments": arguments,
                                "result": result
                            }))
                        
                        # Handle errors
                        elif event_type == "error":
                            error_msg = event.get("error", {}).get("message", "Unknown error")
                            # Don't show buffer too small errors to user
                            if "buffer too small" not in error_msg.lower():
                                await websocket.send_text(json.dumps({
                                    "type": "error",
                                    "message": error_msg
                                }))
                
                except Exception as e:
                    print(f"OpenAI WebSocket error: {e}")
            
            # Run both tasks concurrently
            await asyncio.gather(
                receive_from_client(),
                receive_from_openai()
            )
    
    except WebSocketDisconnect:
        print(f"Client disconnected: user_id={user_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)