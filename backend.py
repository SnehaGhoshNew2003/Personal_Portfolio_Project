from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
import aiosqlite
import os
from datetime import datetime


app = FastAPI(
    title="Sneha Ghosh Portfolio — Contact API",
    version="1.0.0",
    description="Stores contact form submissions from the portfolio website.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "messages.db")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", KEY)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name  TEXT    NOT NULL,
                last_name   TEXT,
                email       TEXT    NOT NULL,
                subject     TEXT    NOT NULL,
                message     TEXT    NOT NULL,
                sent_at     TEXT    NOT NULL,
                ip_address  TEXT
            )
        """)
        await db.commit()


@app.on_event("startup")
async def startup():
    await init_db()
    print(f"  Database ready at: {DB_PATH}")
    print(f"  Admin panel:  GET /api/messages?secret={ADMIN_SECRET}")
    print(f"  Swagger docs: http://localhost:5000/docs")

class ContactRequest(BaseModel):
    firstName: str
    lastName:  str = ""
    email:     EmailStr
    subject:   str
    message:   str

    @field_validator("firstName", "subject", "message")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field cannot be empty.")
        return v.strip()

    @field_validator("lastName")
    @classmethod
    def strip_last(cls, v: str) -> str:
        return v.strip()


class ContactResponse(BaseModel):
    success: bool
    message: str


class MessageRecord(BaseModel):
    id:         int
    first_name: str
    last_name:  str | None
    email:      str
    subject:    str
    message:    str
    sent_at:    str
    ip_address: str | None


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/api/contact", response_model=ContactResponse, status_code=201, tags=["Contact"])
async def submit_contact(payload: ContactRequest, request: Request):
    """
    Receives a contact form submission and persists it to SQLite.
    This endpoint is called by the portfolio's contact form via fetch().
    """
    ip = request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "unknown")
    sent_at = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO messages (first_name, last_name, email, subject, message, sent_at, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.firstName,
                payload.lastName,
                payload.email,
                payload.subject,
                payload.message,
                sent_at,
                ip,
            ),
        )
        await db.commit()

    print(f" [{sent_at}] From: {payload.firstName} {payload.lastName} <{payload.email}> | Subject: {payload.subject}")
    return ContactResponse(success=True, message="Message received! Sneha will get back to you soon.")


@app.get("/api/messages", response_model=list[MessageRecord], tags=["Admin"])
async def list_messages(
    secret: str = Query(..., description="Admin secret key"),
    limit:  int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Returns all stored contact messages — newest first.

    Protected by ?secret= query param.
    Change ADMIN_SECRET env variable before deploying to production.

    Example: GET /api/messages?secret=sneha-admin-2025&limit=20
    """
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized — wrong secret key.")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM messages ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()

    return [dict(r) for r in rows]


@app.delete("/api/messages/{msg_id}", tags=["Admin"])
async def delete_message(
    msg_id: int,
    secret: str = Query(..., description="Admin secret key"),
):
    """Delete a specific message by its ID."""
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    async with aiosqlite.connect(DB_PATH) as db:
        result = await db.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        await db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Message not found.")

    return {"success": True, "message": f"Message {msg_id} deleted."}
