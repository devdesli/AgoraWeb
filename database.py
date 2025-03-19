import sqlite3
import sqlite3

def create_table():
    conn = sqlite3.connect('challenges.db')  # Connect to the database
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            name TEXT,
            mainQuestion TEXT,
            subQuestions TEXT,
            description TEXT,
            endProduct TEXT,
            category TEXT
        )
    ''')

    conn.commit()
    conn.close()

create_table()  # Call the function to create the table