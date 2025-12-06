import threading
from flask import Flask
from app.database import init_db
from app.grpc_server import start_grpc_server
from app.routes import user_bp

app = Flask(__name__)

# Registriamo il blueprint delle rotte
app.register_blueprint(user_bp)

if __name__ == '__main__':
    # 1. Inizializza DB
    init_db()
    
    # 2. Avvia gRPC in background
    grpc_thread = threading.Thread(target=start_grpc_server)
    grpc_thread.daemon = True
    grpc_thread.start()
    
    # 3. Avvia Flask
    print("[REST] Server Flask avviato su porta 5000")
    app.run(host='0.0.0.0', port=5000)