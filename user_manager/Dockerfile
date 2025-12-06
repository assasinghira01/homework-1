FROM python:3.10-slim

WORKDIR /service

COPY user_manager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY user_manager/app ./app


COPY protos/usermanager.proto .
# Generiamo i file Python NELLA ROOT 
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. usermanager.proto
# --------------------

ENV PYTHONPATH=/service
CMD ["python", "-m", "app.main"]
