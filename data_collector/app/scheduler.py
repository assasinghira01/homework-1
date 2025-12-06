import time
import requests
import json
from datetime import datetime
from app.database import get_db_connection


URL_ARRIVAL = "https://opensky-network.org/api/flights/arrival"
URL_DEPARTURE = "https://opensky-network.org/api/flights/departure"

def fetch_opensky_data():
    print("[Worker] Avviato.")
    
    while True:
        try:
            conn = get_db_connection()
            if not conn:
                time.sleep(5)
                continue

            cur = conn.cursor()
            cur.execute("SELECT DISTINCT airport_code FROM interests")
            rows = cur.fetchall()
            airports = [row[0] for row in rows]
            cur.close()
            conn.close()

            if not airports:
                print("[Worker] Nessun interesse attivo.")
                time.sleep(30)
                continue

            
            # Le API free danno solo dati passati.
            # Chiediamo una finestra di 2 ore riferita a IERI.
            now_ts = int(time.time())
            end_ts = now_ts - 86400      # Esattamente 24 ore fa
            begin_ts = end_ts - 7200     # Finestra di 2 ore per evitare troppi dati

            print(f"[Worker] Cerco dati per: {airports}")

            for airport in airports:
                flights_found = []

                # 1. cerchiamo arrivi
                try:
                    params = {"airport": airport, "begin": begin_ts, "end": end_ts}
                    r = requests.get(URL_ARRIVAL, params=params, timeout=15)
                    
                    if r.status_code == 200:
                        data = r.json()
                        for f in data:
                            f['type'] = 'ARRIVAL'       
                            f['source'] = 'OPENSKY_REAL_HISTORY'
                            flights_found.append(f)
                        print(f"[Worker] -> {airport}: Trovati {len(data)} Arrivi.")
                    elif r.status_code == 404:
                        print(f"[Worker] -> {airport}: Nessun arrivo (Lista vuota).")
                except Exception as e:
                    print(f"[Worker] Errore API Arrivi: {e}")

                # 2. cerchiamo partenze
                try:
                    params = {"airport": airport, "begin": begin_ts, "end": end_ts}
                    r = requests.get(URL_DEPARTURE, params=params, timeout=15)
                    
                    if r.status_code == 200:
                        data = r.json()
                        for f in data:
                            f['type'] = 'DEPARTURE'     
                            f['source'] = 'OPENSKY_REAL_HISTORY'
                            flights_found.append(f)
                        print(f"[Worker] -> {airport}: Trovate {len(data)} Partenze.")
                    elif r.status_code == 404:
                        print(f"[Worker] -> {airport}: Nessuna partenza (Lista vuota).")
                except Exception as e:
                    print(f"[Worker] Errore API Partenze: {e}")

                # 3. salviamo i dati
                if flights_found:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    # Salviamo i primi 10
                    json_str = json.dumps(flights_found[:10])
                    
                    cur.execute("""
                        INSERT INTO flights (airport_code, flight_json, obs_time)
                        VALUES (%s, %s, %s)
                    """, (airport, json_str, datetime.utcnow()))
                    
                    conn.commit()
                    cur.close()
                    conn.close()
                    print(f"[Worker] Salvati dati  per {airport} ")
                else:
                    print(f"[Worker] Nessun dato trovato per {airport}.")

        except Exception as e:
            print(f"[Worker] Errore critico: {e}")

        # Pausa 
        print("[Worker] Attendo 60 secondi...")
        time.sleep(60)