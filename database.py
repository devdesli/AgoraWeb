import sqlite3
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)


def create_table():
    conn = sqlite3.connect('challenges.db')
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

def insert_challenge(title, name, mainQuestion, subQuestions, description, endProduct, category):
    conn = sqlite3.connect('challenges.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO challenges (title, name, mainQuestion, subQuestions, description, endProduct, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, name, mainQuestion, subQuestions, description, endProduct, category))
    conn.commit()
    conn.close()

@app.route('/add_challenge', methods=['POST'])
def add_challenge():
    data = request.get_json()  # Get the JSON data from the request

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    title = data.get('title')
    name = data.get('name')
    mainQuestion = data.get('mainQuestion')
    subQuestions = data.get('subQuestions')
    description = data.get('description')
    endProduct = data.get('endProduct')
    category = data.get('category')

    if not all([title, name, mainQuestion, subQuestions, description, endProduct, category]):
        return jsonify({'error': 'Missing data fields'}), 400

    insert_challenge(title, name, mainQuestion, subQuestions, description, endProduct, category)
    return jsonify({'message': 'Challenge added successfully'}), 201

if __name__ == '__main__':
    create_table()  # Create the table when the app starts
    app.run(debug=True)