from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)

# def init_db():
#     conn = sqlite3.connect('chat.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             fullname TEXT NOT NULL,
#             username TEXT NOT NULL UNIQUE,
#             password TEXT NOT NULL
#         )
#     ''')
#     conn.commit()
#     conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    # init_db()
    app.run(debug=True)