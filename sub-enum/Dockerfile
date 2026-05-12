# Use a base image with Go installed
FROM golang:1.25-alpine AS builder

# Install dependencies for building tools
RUN apk add --no-cache git build-base rust cargo python3 py3-pip perl

# Install Go-based tools
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
RUN go install -v github.com/tomnomnom/assetfinder@latest
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
RUN go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
RUN go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest

# Install Findomain from GitHub source
RUN git clone https://github.com/Findomain/Findomain.git /tmp/findomain && \
    cd /tmp/findomain && \
    cargo build --release && \
    cp target/release/findomain /usr/local/bin/ && \
    cd / && \
    rm -rf /tmp/findomain

# Final Stage: minimal runtime image
FROM alpine:3.20

# Create a non-root user for safety
RUN addgroup -S subenum && adduser -S -G subenum subenum

# Install runtime dependencies
RUN apk add --no-cache python3 py3-pip git bash ca-certificates

# Ensure /usr/local/bin is present in PATH and owned correctly
ENV HOME=/home/subenum
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/bin:$HOME/.local/bin:$PATH

RUN mkdir -p $HOME && chown subenum:subenum $HOME

# Copy Go binaries from builder
COPY --from=builder /go/bin/subfinder /usr/local/bin/
COPY --from=builder /go/bin/assetfinder /usr/local/bin/
COPY --from=builder /go/bin/httpx /usr/local/bin/
COPY --from=builder /go/bin/dnsx /usr/local/bin/
COPY --from=builder /go/bin/chaos /usr/local/bin/

# Copy Findomain from builder (built to /usr/local/bin during cargo build)
COPY --from=builder /usr/local/bin/findomain /usr/local/bin/

# Install Python tools (altdns) using the container's Python interpreter
RUN python3 -m pip install --no-cache-dir --break-system-packages git+https://github.com/infosec-au/altdns.git

# Copy application into image and install package as the system Python
COPY . /app
WORKDIR /app
RUN python3 -m pip install --no-cache-dir --break-system-packages .

# Make workspace dir for tools and set ownership
RUN mkdir -p $HOME/.sub-enum && chown -R subenum:subenum $HOME/.sub-enum

# Switch to non-root user
USER subenum

# Entrypoint: run the installed console script
ENTRYPOINT ["sub-enum"]
CMD ["-h"]
