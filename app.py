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
        
        # [수정됨] game_id 컬럼을 추가했습니다! (어떤 게임인지 구분용)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id SERIAL PRIMARY KEY,
                game_id VARCHAR(50) NOT NULL,
                score INT NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized with game_id.")
    except Exception as e:
        print(f"Error initializing database: {e}")

# --- API ---

@app.route('/submit', methods=['POST'])
def submit_score():
    try:
        data = request.json
        score = data.get('score')
        game_id = data.get('game_id') # [추가] 게임 이름을 받습니다.

        if score is None or game_id is None:
            return jsonify({'error': 'Score and game_id are required'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # 1. 점수 저장 (게임 이름도 같이 저장)
        cur.execute('INSERT INTO scores (game_id, score) VALUES (%s, %s)', (game_id, score))
        
        # 2. 내 랭킹 계산 (내 게임이랑 같은 게임 중에서만 등수 계산!)
        cur.execute('SELECT COUNT(*) FROM scores WHERE game_id = %s AND score > %s', (game_id, score))
        rank = cur.fetchone()[0] + 1
        
        # 3. 그 게임의 전체 플레이어 수
        cur.execute('SELECT COUNT(*) FROM scores WHERE game_id = %s', (game_id,))
        total = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'rank': rank, 'total': total})

    except Exception as e:
        print(f"Error in /submit: {e}")
        return jsonify({'error': str(e)}), 500

initialize_database()
