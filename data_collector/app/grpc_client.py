import os
import grpc
from uuid import uuid4

import usermanager_pb2
import usermanager_pb2_grpc

USER_MANAGER_HOST = os.getenv("USER_MANAGER_HOST", "user-manager")
USER_MANAGER_PORT = os.getenv("USER_MANAGER_GRPC_PORT", "50051")

def check_user_exists_grpc(email):
    """Controlla se un utente esiste via gRPC rispettando AT-MOST-ONCE."""
    target = f"{USER_MANAGER_HOST}:{USER_MANAGER_PORT}"
    print(f"[gRPC] Verifico utente: {email} su {target}")

    try:
        # Apertura canale sicura
        with grpc.insecure_channel(target) as channel:
            stub = usermanager_pb2_grpc.UserManagerStub(channel)

            # Request con ID univoco (AT-MOST-ONCE)
            request = usermanager_pb2.UserCheckRequest(
                email=email,
                request_id=str(uuid4())
            )

            # Timeout necessario
            response = stub.CheckUser(request, timeout=5)

            return response.exists

    except grpc.RpcError as e:
        print(f"[gRPC] Errore RPC: {e.code()} - {e.details()}")
        return False

    except Exception as e:
        print(f"[gRPC] Errore generale: {e}")
        return False
