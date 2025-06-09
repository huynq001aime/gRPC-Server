FROM python:3.9.7-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    curl \
    wget \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libzstd-dev \
    && rm -rf /var/lib/apt/lists/*


# Install Golang
ENV GO_VERSION=1.24.4
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:$PATH"


WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY go.mod go.sum ./

RUN go get -tool github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway && \
    go get -tool github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-openapiv2 && \
    go get -tool google.golang.org/protobuf/cmd/protoc-gen-go && \
    go get -tool google.golang.org/grpc/cmd/protoc-gen-go-grpc

RUN go install tool

ENV PATH="/root/go/bin:${PATH}"

COPY . .

RUN git clone https://github.com/googleapis/googleapis.git


# gRPC
EXPOSE 50051

# gRPC Gateway
EXPOSE 8080


CMD ["sh", "-c", "python server.py & go run main.go"]
