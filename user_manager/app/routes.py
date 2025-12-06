from flask import Blueprint, request, jsonify
from app.database import get_db_connection

# Definiamo un Blueprint (un gruppo di rotte)
user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/register', methods=['POST'])
def register_user():
    data = request.json or {}
    email = data.get('email')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    
    if not email:
        return jsonify({"error": "Email mancante"}), 400

    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Politica At-Most-Once
            cur.execute("INSERT INTO users (email, first_name, last_name) VALUES (%s, %s, %s) ON CONFLICT (email) DO NOTHING", (email, first_name, last_name))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"message": f"Utente {email} registrato correttamente (o già presente)."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Errore DB"}), 500

@user_bp.route('/user/<email>', methods=['DELETE'])
def delete_user(email):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"message": f"Utente {email} cancellato"}), 200

# Utility per vedere gli utenti (Debug)
@user_bp.route('/users', methods=['GET'])
def list_users():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT email, first_name, last_name FROM users")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows), 200
    return jsonify([]), 500