import grpc
from concurrent import futures
from uuid import uuid4
import usermanager_pb2
import usermanager_pb2_grpc
from app.database import get_db_connection

# Cache in memoria per AT-MOST-ONCE
recent_requests = {}

class UserManagerServicer(usermanager_pb2_grpc.UserManagerServicer):

    def CheckUser(self, request, context):
        email = request.email
        req_id = request.request_id

        print(f"[gRPC] Richiesta verifica per: {email} | request_id={req_id}")

        # 1) AT-MOST-ONCE
        if req_id in recent_requests:
            print("[gRPC] Risposta trovata in cache, ritorno quella precedente")
            return recent_requests[req_id]

        # 2) Logica standard: controllo utente
        exists = False
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                exists = True
            cur.close()
            conn.close()

        reply = usermanager_pb2.UserCheckReply(exists=exists)

        # 3) Salva in cache per futuri retry
        recent_requests[req_id] = reply

        return reply


def start_grpc_server():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )
    usermanager_pb2_grpc.add_UserManagerServicer_to_server(
        UserManagerServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    print("[gRPC] Server avviato sulla porta 50051")
    server.start()
    server.wait_for_termination()
