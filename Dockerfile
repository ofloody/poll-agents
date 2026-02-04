FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .
RUN pip install --no-cache-dir supabase>=2.0

# Copy source code
COPY src/ src/

# Install the package
RUN pip install --no-cache-dir -e ".[supabase]"

# Expose ports: 8080 for health checks, 8765 for WebSocket
EXPOSE 8080 8765

# Run the server
CMD ["poll-agents"]
