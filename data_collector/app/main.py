import threading
import datetime
from flask import Flask, request, jsonify

from app.database import init_db, get_db_connection
from app.grpc_client import check_user_exists_grpc
from app.scheduler import fetch_opensky_data

app = Flask(__name__)


# 1) ATTIVAZIONE MONITORAGGIO

@app.route('/monitor', methods=['POST'])
def add_interest():
    data = request.json or {}
    email = data.get('email')
    airport = data.get('airport')

    if not email or not airport:
        return jsonify({"error": "Dati mancanti"}), 400

    airport = airport.upper()

    # Verifica via gRPC (USER MANAGER)
    if not check_user_exists_grpc(email):
        return jsonify({"error": "Utente non registrato!"}), 404

    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO interests (user_email, airport_code)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (email, airport))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"message": f"Monitoraggio attivato: {email} -> {airport}"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Errore DB"}), 500


@app.route('/flights/last', methods=['GET'])
def get_last_flight():
    airport = request.args.get('airport')
    flight_type = request.args.get('type') # Opzionale: 'ARRIVAL' o 'DEPARTURE'
    
    if not airport: return jsonify({"error": "Parametro 'airport' mancante"}), 400

    airport = airport.upper()

    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # 1. Recupera l'ultimo pacchetto dati salvato
            cur.execute("""
                SELECT flight_json, obs_time 
                FROM flights 
                WHERE airport_code=%s 
                ORDER BY id DESC 
                LIMIT 1
            """, (airport,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                all_flights = row[0] 
                time_val = row[1]
                
                
                flights_to_check = all_flights
                if flight_type:
                    # Filtra la lista in Python in base al tipo
                    flights_to_check = [f for f in all_flights if f.get('type') == flight_type]

                if flights_to_check:
                    # RESTITUISCE SOLO IL PRIMO ELEMENTO DELLA LISTA FILTRATA (ultimo volo)
                    return jsonify({
                        "airport": airport,
                        "type": flight_type or "ALL_SNAPSHOT",
                        "flight": flights_to_check[0], # (Ultimo Arrivo/Partenza)
                        "time": time_val
                    }), 200
            # Se la riga esiste ma la lista filtrata è vuota, restituisce 404
            return jsonify({"message": f"Nessun volo '{flight_type}' trovato nell'ultimo snapshot."}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Nessun volo trovato"}), 404


# 3) MEDIA VOI NSU ULTIMI N GIORNI (Non richiede modifiche al codice)

@app.route('/flights/average', methods=['GET'])
def get_average():
    airport = request.args.get('airport')
    flight_type = request.args.get('type') # Opzionale
    
    try: days = int(request.args.get('days', '7'))
    except ValueError: return jsonify({"error": "'days' deve essere un numero"}), 400

    if not airport: return jsonify({"error": "Parametro 'airport' mancante"}), 400

    airport = airport.upper()

    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            limit_date = datetime.now() - datetime.timedelta(days=days)
            
            # . Recuperiamo tutti i voli degli ultimi X giorni
            cur.execute("SELECT flight_json FROM flights WHERE airport_code = %s AND obs_time >= %s", (airport, limit_date))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            total_count = 0
            for r in rows:
                flights_list = r[0] 
                # Contiamo solo quelli che corrispondono al tipo richiesto
                total_count += sum(1 for f in flights_list if not flight_type or f.get('type') == flight_type)

            avg = total_count / days if days > 0 else 0
            
            return jsonify({
                "airport": airport,
                "days_analyzed": days,
                "filter_type": flight_type if flight_type else "ALL",
                "total_flights_found": total_count,
                "average_flights_per_day": round(avg, 2)
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Errore DB"}), 500


# 4) DEBUG - FORZA RACCOLTA

@app.route('/collect', methods=['POST'])
def force_collect():
    # Attiva una raccolta immediata
    threading.Thread(target=fetch_opensky_data, daemon=True).start()
    return jsonify({"message": "Raccolta forzata avviata"}), 200


# AVVIO

if __name__ == '__main__':
    init_db()

    worker = threading.Thread(target=fetch_opensky_data)
    worker.daemon = True
    worker.start()

    app.run(host='0.0.0.0', port=5000)
