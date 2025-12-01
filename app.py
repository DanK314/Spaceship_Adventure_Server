import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def initialize_database():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # [수정됨] 'player' 컬럼을 테이블 정의에서 삭제합니다.
        cur.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id SERIAL PRIMARY KEY,
                score INT NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("Database table (no player) initialized.")
    except Exception as e:
        print(f"Error initializing database: {e}")

# --- API (게임이 접속할 주소) ---

@app.route('/submit', methods=['POST'])
def submit_score():
    try:
        data = request.json
        
        # [수정됨] 'player'를 받는 부분을 삭제하고 'score'만 받습니다.
        score = data.get('score')

        # [수정됨] 'player' 체크를 삭제하고 'score'만 체크합니다.
        if score is None:
            return jsonify({'error': 'Score is required'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # [수정됨] 1. 'score'만 DB에 삽입합니다.
        cur.execute('INSERT INTO scores (score) VALUES (%s)', (score,))
        
        # 2. 랭킹 계산 (변경 없음)
        cur.execute('SELECT COUNT(*) FROM scores WHERE score > %s', (score,))
        rank = cur.fetchone()[0] + 1
        
        # 3. 전체 인원 수 계산 (변경 없음)
        cur.execute('SELECT COUNT(*) FROM scores')
        total = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        # 4. 랭킹 응답 (변경 없음)
        return jsonify({'rank': rank, 'total': total})

    except Exception as e:
        print(f"Error in /submit: {e}")
        return jsonify({'error': 'Server error'}), 500

initialize_database()
