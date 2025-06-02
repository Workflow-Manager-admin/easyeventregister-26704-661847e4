from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'easyeventregister.db')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Initialization
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            participant_name TEXT NOT NULL,
            contact_info TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
        """
    )
    # Seed the database with demo events if empty
    cur.execute("SELECT COUNT(*) FROM events")
    (count,) = cur.fetchone()
    if count == 0:
        demo_events = [
            ("Tech Expo 2024", "2024-08-10", "Hall A", "Annual technology showcase."),
            ("Art Gala", "2024-09-15", "Gallery 2", "Modern art exhibit."),
            ("Music Fest", "2024-07-01", "Central Park", "Open-air music festival."),
        ]
        cur.executemany("INSERT INTO events (name, date, location, description) VALUES (?, ?, ?, ?)", demo_events)
    conn.commit()
    conn.close()

init_db()

# Event models
class Event(BaseModel):
    id: int
    name: str
    date: str
    location: str
    description: Optional[str] = None

class EventOut(BaseModel):
    id: int
    name: str
    date: str
    location: str
    description: Optional[str] = None

class RegisterPayload(BaseModel):
    participant_name: str = Field(..., min_length=1)
    contact_info: str = Field(..., min_length=1)

class RegistrationOut(BaseModel):
    id: int
    event_id: int
    participant_name: str
    contact_info: str

# PUBLIC_INTERFACE
@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.get("/events", response_model=List[EventOut], tags=["Events"])
def list_events():
    """List all events."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY date ASC")
    events = [EventOut(**dict(row)) for row in cur.fetchall()]
    conn.close()
    return events

# PUBLIC_INTERFACE
@app.post("/events/{event_id}/register", response_model=RegistrationOut, status_code=status.HTTP_201_CREATED, tags=["Registrations"])
def register_for_event(event_id: int, registration: RegisterPayload):
    """Register for an event by event_id."""
    conn = get_db()
    cur = conn.cursor()
    # Verify event exists
    cur.execute("SELECT id FROM events WHERE id=?", (event_id,))
    if cur.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Event not found")
    # Insert registration
    cur.execute(
        "INSERT INTO registrations (event_id, participant_name, contact_info) VALUES (?, ?, ?)",
        (event_id, registration.participant_name, registration.contact_info)
    )
    reg_id = cur.lastrowid
    conn.commit()
    # Fetch registration for response
    cur.execute(
        "SELECT * FROM registrations WHERE id=?",
        (reg_id,)
    )
    row = cur.fetchone()
    conn.close()
    return RegistrationOut(**dict(row))

# PUBLIC_INTERFACE
@app.get("/events/{event_id}/registrations", response_model=List[RegistrationOut], tags=["Registrations"])
def list_registrations(event_id: int):
    """List all registrations for a specific event."""
    conn = get_db()
    cur = conn.cursor()
    # Verify event exists
    cur.execute("SELECT id FROM events WHERE id=?", (event_id,))
    if cur.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Event not found")
    cur.execute(
        "SELECT * FROM registrations WHERE event_id=?",
        (event_id,)
    )
    registrations = [RegistrationOut(**dict(row)) for row in cur.fetchall()]
    conn.close()
    return registrations
