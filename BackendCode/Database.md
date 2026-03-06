To check your players.db directly in your Termux or VPS terminal, you use the SQLite3 Command Line Interface. Since SQLite stores everything in a single file, you can jump in, run a query, and see your data instantly.
1. Open the Database
Navigate to the folder where your main.py is located and run:
sqlite3 players.db

You will see a prompt like sqlite>.
2. Formating the Output (Crucial for Readability)
By default, the output is messy. Run these "dot commands" first to make it look like a clean table:
.mode column
.headers on

3. Check User Balances and Total Profit
To see how much TON your users have "earned" (which represents your liability/payouts), run:
SELECT id, spins, balance FROM users;

To see the Total TON currently held by all users combined:
SELECT SUM(balance) AS total_user_debt FROM users;

4. Check Pending Withdrawals
To see who you need to pay right now:
SELECT * FROM withdrawals WHERE status = 'pending';

Admin "Cheat Sheet" for Terminal
If you want to quickly see the data without staying inside the SQLite prompt, you can run a "one-liner" directly from your Bash terminal:
 * See top 10 richest users:
   sqlite3 players.db "SELECT * FROM users ORDER BY balance DESC LIMIT 10;"
 * See total number of players:
   sqlite3 players.db "SELECT COUNT(*) FROM users;"
 * Exit the SQLite prompt: Type .exit or press Ctrl+D.
What's Next?
Now that you can monitor your data, you are ready to launch! I recommend setting up a "Daily Bonus" logic next so users have a reason to open your bot every single day, even if they run out of spins. Would you like the code for that?
How to Use SQLite3 in Terminal
This video is helpful because it shows you exactly how to navigate the SQLite command line, run queries, and format your data so it's easy to read in a terminal environment.

YouTube video views will be stored in your YouTube History, and your data will be stored and used by YouTube according to its Terms of Service
