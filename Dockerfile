FROM golang:1.25-alpine AS builder

ARG SUBFINDER_VERSION=v2.14.0
ARG DNSX_VERSION=v1.3.0
ARG HTTPX_VERSION=v1.10.0
ARG ALTERX_VERSION=v0.0.6
ARG PUREDNS_VERSION=v2.1.1
ARG FINDOMAIN_VERSION=10.0.1
ARG MASSDNS_COMMIT=6bfa47197d78e68b79041d494e280174cb2d6ae1

RUN apk add --no-cache git build-base rust cargo perl openssl-dev pkgconfig

RUN GOBIN=/out go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@${SUBFINDER_VERSION} && \
    GOBIN=/out go install github.com/projectdiscovery/dnsx/cmd/dnsx@${DNSX_VERSION} && \
    GOBIN=/out go install github.com/projectdiscovery/httpx/cmd/httpx@${HTTPX_VERSION} && \
    GOBIN=/out go install github.com/projectdiscovery/alterx/cmd/alterx@${ALTERX_VERSION} && \
    GOBIN=/out go install github.com/d3mondev/puredns/v2@${PUREDNS_VERSION}

RUN git clone https://github.com/blechschmidt/massdns.git /tmp/massdns && \
    cd /tmp/massdns && \
    git checkout ${MASSDNS_COMMIT} && \
    make && \
    cp bin/massdns /out/massdns

RUN git clone --branch ${FINDOMAIN_VERSION} --depth 1 https://github.com/Findomain/Findomain.git /tmp/findomain && \
    cd /tmp/findomain && \
    cargo build --release && \
    cp target/release/findomain /out/findomain

FROM alpine:3.22

RUN addgroup -S subenum && adduser -S -G subenum subenum && \
    apk add --no-cache python3 py3-pip ca-certificates libgcc libstdc++

COPY --from=builder /out/ /usr/local/bin/
COPY . /app
WORKDIR /app
RUN python3 -m pip install --no-cache-dir --break-system-packages . && \
    mkdir -p /home/subenum/.sub-enum /home/subenum/.config/subfinder /scans && \
    chown -R subenum:subenum /home/subenum /scans

ENV HOME=/home/subenum
USER subenum
WORKDIR /scans
ENTRYPOINT ["sub-enum"]
CMD ["--help"]
