from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import requests

app = FastAPI()

# 1. SETTINGS - CHANGE THESE
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # Get your ID from @userinfobot on Telegram
API_URL = "http://0.0.0.0:8000"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect('players.db')
    return conn

# Initialize Database with Withdrawal Table
db = get_db()
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, spins INTEGER DEFAULT 5, balance REAL DEFAULT 0.0)")
db.execute("CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, address TEXT, amount REAL, status TEXT DEFAULT 'pending')")
db.commit()

@app.get("/user/{user_id}")
def get_user(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT spins, balance FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        conn.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        row = (5, 0.0)
    return {"spins": row[0], "balance": row[1]}

@app.post("/spin/{user_id}")
def spin(user_id: int):
    conn = get_db()
    user = conn.execute("SELECT spins, balance FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or user[0] <= 0:
        raise HTTPException(status_code=400, detail="No spins left")

    # Prizes
    prizes = [("0.01", 0.01), ("0", 0.0), ("0.05", 0.05), ("JACKPOT", 0.1), ("0.02", 0.02), ("0", 0.0)]
    import random
    win_label, win_amount = random.choice(prizes)
    
    new_spins = user[0] - 1
    new_balance = user[1] + win_amount
    conn.execute("UPDATE users SET spins = ?, balance = ? WHERE id = ?", (new_spins, new_balance, user_id))
    conn.commit()
    return {"win_label": win_label, "new_spins": new_spins, "new_balance": new_balance}

@app.post("/withdraw")
async def withdraw(data: dict):
    user_id = data['user_id']
    address = data['address']
    conn = get_db()
    user = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if user and user[0] >= 0.5:
        amount = user[0]
        # Reset balance and log withdrawal
        conn.execute("UPDATE users SET balance = 0 WHERE id = ?", (user_id,))
        conn.execute("INSERT INTO withdrawals (user_id, address, amount) VALUES (?, ?, ?)", (user_id, address, amount))
        conn.commit()
        
        # ALERT ADMIN VIA TELEGRAM
        msg = f"🚨 **NEW WITHDRAWAL**\nUser: {user_id}\nAmount: {amount} TON\nWallet: `{address}`"
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text={msg}&parse_mode=Markdown")
        
        return {"status": "ok"}
    raise HTTPException(status_code=400, detail="Insufficient balance")

@app.post("/add_spin/{user_id}")
def add_spin(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET spins = spins + 1 WHERE id = ?", (user_id,))
    conn.commit()
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
