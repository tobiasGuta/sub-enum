# Use a base image with Go installed
FROM golang:1.23-alpine AS builder

# Install dependencies for building tools
RUN apk add --no-cache git build-base rust cargo python3 py3-pip

# Install Go-based tools
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
RUN go install -v github.com/tomnomnom/assetfinder@latest
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
RUN go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
RUN go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest

# Install Findomain (Rust)
# Note: Findomain binary is often easier to just download, but building ensures compatibility
# Downloading binary to save build time in this example, or build if preferred.
# Using pre-built binary for Alpine if available, otherwise build.
# Let's build it to be safe or use the one from the script logic? 
# Docker best practice is to build or download in the Dockerfile.
RUN cargo install findomain

# Final Stage
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache python3 py3-pip git bash

# Copy Go binaries
COPY --from=builder /go/bin/subfinder /usr/local/bin/
COPY --from=builder /go/bin/assetfinder /usr/local/bin/
COPY --from=builder /go/bin/httpx /usr/local/bin/
COPY --from=builder /go/bin/dnsx /usr/local/bin/
COPY --from=builder /go/bin/chaos /usr/local/bin/

# Copy Rust binaries
COPY --from=builder /root/.cargo/bin/findomain /usr/local/bin/

# Install Python tools
# Sublist3r
WORKDIR /tools
RUN git clone https://github.com/aboul3la/Sublist3r.git
WORKDIR /tools/Sublist3r
RUN pip3 install -r requirements.txt --break-system-packages
RUN python3 setup.py install
RUN ln -s /tools/Sublist3r/sublist3r.py /usr/local/bin/sublist3r

# altdns
RUN pip3 install git+https://github.com/infosec-au/altdns.git --break-system-packages

# Copy the main script
WORKDIR /app
COPY sub_enum.py .
RUN chmod +x sub_enum.py

# Entrypoint
ENTRYPOINT ["./sub_enum.py"]
CMD ["-h"]
