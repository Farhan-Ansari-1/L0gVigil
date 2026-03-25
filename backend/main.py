from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pathlib import Path

app = FastAPI(title="L0gVigil Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "../blocked_ips.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read_root():
    return {"status": "L0gVigil API is running"}

@app.get("/attacks")
def get_attacks():
    conn = get_db_connection()
    try:
        attacks = conn.execute(
            "SELECT * FROM blocked_ips ORDER BY id DESC LIMIT 50"
        ).fetchall()
        return [dict(row) for row in attacks]
    finally:
        conn.close()

@app.get("/stats")
def get_stats():
    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM blocked_ips").fetchone()[0]
        unique_ips = conn.execute("SELECT COUNT(DISTINCT ip) FROM blocked_ips").fetchone()[0]
        return {
            "total_blocks": total,
            "unique_attackers": unique_ips,
        }
    finally:
        conn.close()

@app.delete("/attacks/{attack_id}")
def delete_attack(attack_id: int):
    conn = get_db_connection()
    try:
        attack = conn.execute(
            "SELECT ip FROM blocked_ips WHERE id = ?",
            (attack_id,)
        ).fetchone()

        if not attack:
            raise HTTPException(status_code=404, detail="Attack not found")

        conn.execute("DELETE FROM blocked_ips WHERE id = ?", (attack_id,))
        conn.commit()
        return {"message": f"Attack {attack_id} removed from dashboard"}
    finally:
        conn.close()
