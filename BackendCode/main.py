from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import random

app = FastAPI()

# IMPORTANT: Allow GitHub Pages to talk to your VPS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect('players.db')
    return conn

# Init Database
db = get_db()
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, spins INTEGER DEFAULT 5, balance REAL DEFAULT 0.0)")
db.commit()

@app.get("/user/{user_id}")
def get_user(user_id: int):
    conn = get_db()
    cursor = conn.execute("SELECT spins, balance FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
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

    # Logic: Prizes and Probabilities
    prizes = [("0.01", 0.01), ("0", 0.0), ("0.05", 0.05), ("JACKPOT", 0.1), ("0.02", 0.02), ("0", 0.0)]
    win_label, win_amount = random.choice(prizes)
    
    new_spins = user[0] - 1
    new_balance = user[1] + win_amount
    
    conn.execute("UPDATE users SET spins = ?, balance = ? WHERE id = ?", (new_spins, new_balance, user_id))
    conn.commit()
    return {"win_label": win_label, "new_spins": new_spins, "new_balance": new_balance}

@app.post("/add_spin/{user_id}")
def add_spin(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET spins = spins + 1 WHERE id = ?", (user_id,))
    conn.commit()
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
