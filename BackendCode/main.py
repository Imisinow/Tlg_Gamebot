from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import time
import requests

app = FastAPI()

# --- CONFIG ---
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789 
# --------------

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    return sqlite3.connect('players.db')

# Init DB with Leaderboard support
with get_db() as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, spins INTEGER DEFAULT 5, balance REAL DEFAULT 0.0, last_bonus INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, address TEXT, amount REAL, status TEXT DEFAULT 'pending')")
    try: conn.execute("ALTER TABLE users ADD COLUMN username TEXT")
    except: pass

@app.get("/user/{user_id}")
def get_user(user_id: int, name: str = "Player"):
    with get_db() as conn:
        row = conn.execute("SELECT spins, balance, last_bonus FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            conn.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, name))
            conn.commit()
            row = (5, 0.0, 0)
        else:
            # Update name in case they changed it on Telegram
            conn.execute("UPDATE users SET username = ? WHERE id = ?", (name, user_id))
            conn.commit()
        
        can_claim = (int(time.time()) - row[2]) >= 86400
        return {"spins": row[0], "balance": row[1], "bonus_available": can_claim}

@app.get("/leaderboard")
def get_leaderboard():
    with get_db() as conn:
        # Get Top 10 users by balance
        top_users = conn.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10").fetchall()
        return [{"name": r[0] or "Anonymous", "balance": round(r[1], 3)} for r in top_users]

@app.post("/spin/{user_id}")
def spin(user_id: int):
    with get_db() as conn:
        user = conn.execute("SELECT spins, balance FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or user[0] <= 0: raise HTTPException(status_code=400, detail="No spins!")
        
        win_amount = [0.01, 0, 0.05, 0.1, 0.02, 0][int(time.time()) % 6] # Simple random logic
        conn.execute("UPDATE users SET spins = spins - 1, balance = balance + ? WHERE id = ?", (win_amount, user_id))
        conn.commit()
        return {"win": win_amount}

@app.post("/claim_daily/{user_id}")
def claim(user_id: int):
    now = int(time.time())
    with get_db() as conn:
        user = conn.execute("SELECT last_bonus FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and (now - user[0]) >= 86400:
            conn.execute("UPDATE users SET spins = spins + 3, last_bonus = ? WHERE id = ?", (now, user_id))
            conn.commit()
            return {"status": "ok"}
    raise HTTPException(status_code=400, detail="Not ready yet")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
