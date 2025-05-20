import sqlite3

conn = sqlite3.connect("minesweeper_stats.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        result TEXT NOT NULL,
        duration REAL NOT NULL
    )
''')

conn.commit()
