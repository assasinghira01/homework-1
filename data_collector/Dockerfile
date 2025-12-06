FROM python:3.10-slim

WORKDIR /service

COPY data_collector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data_collector/app ./app

COPY protos/usermanager.proto .

RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. usermanager.proto
# --------------------

ENV PYTHONPATH=/service
CMD ["python", "-m", "app.main"]
