FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install the package with supabase dependencies
RUN pip install --no-cache-dir ".[supabase]"

# Expose WebSocket port (Render uses 10000 by default)
EXPOSE 10000

# Unbuffered Python output for Docker logs
ENV PYTHONUNBUFFERED=1

# Run the server
CMD ["poll-agents"]
