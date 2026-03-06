from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import random
import time
import requests

app = FastAPI()

# --- CONFIGURATION ---
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # Get from @userinfobot
# ---------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect('players.db')
    return conn

# Initialize/Update Database
with get_db() as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, spins INTEGER DEFAULT 5, balance REAL DEFAULT 0.0, last_bonus INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, address TEXT, amount REAL, status TEXT DEFAULT 'pending')")
    # Check if last_bonus column exists (for older databases)
    try:
        conn.execute("ALTER TABLE users ADD COLUMN last_bonus INTEGER DEFAULT 0")
    except:
        pass 

@app.get("/user/{user_id}")
def get_user(user_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT spins, balance, last_bonus FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            conn.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
            conn.commit()
            row = (5, 0.0, 0)
        
        # Check if bonus is available (24 hours = 86400 seconds)
        can_claim = (int(time.time()) - row[2]) >= 86400
        return {"spins": row[0], "balance": row[1], "bonus_available": can_claim}

@app.post("/claim_daily/{user_id}")
def claim_daily(user_id: int):
    now = int(time.time())
    with get_db() as conn:
        user = conn.execute("SELECT last_bonus FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and (now - user[0]) >= 86400:
            conn.execute("UPDATE users SET spins = spins + 3, last_bonus = ? WHERE id = ?", (now, user_id))
            conn.commit()
            return {"status": "success", "message": "+3 Spins added!"}
        raise HTTPException(status_code=400, detail="Bonus already claimed today!")

@app.post("/spin/{user_id}")
def spin(user_id: int):
    with get_db() as conn:
        user = conn.execute("SELECT spins, balance FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or user[0] <= 0:
            raise HTTPException(status_code=400, detail="No spins left")

        prizes = [("0.01", 0.01), ("0", 0.0), ("0.05", 0.05), ("JACKPOT", 0.1), ("0.02", 0.02), ("0", 0.0)]
        win_label, win_amount = random.choice(prizes)
        
        conn.execute("UPDATE users SET spins = spins - 1, balance = balance + ? WHERE id = ?", (win_amount, user_id))
        conn.commit()
        
        # Get updated data
        updated = conn.execute("SELECT spins, balance FROM users WHERE id = ?", (user_id,)).fetchone()
        return {"win_label": win_label, "new_spins": updated[0], "new_balance": updated[1]}

@app.post("/withdraw")
async def withdraw(data: dict):
    user_id, address = data['user_id'], data['address']
    with get_db() as conn:
        user = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and user[0] >= 0.5:
            amount = user[0]
            conn.execute("UPDATE users SET balance = 0 WHERE id = ?", (user_id,))
            conn.execute("INSERT INTO withdrawals (user_id, address, amount) VALUES (?, ?, ?)", (user_id, address, amount))
            conn.commit()
            requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text=💸 Withdrawal: {amount} TON to {address}")
            return {"status": "ok"}
    raise HTTPException(status_code=400, detail="Insufficient balance")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
