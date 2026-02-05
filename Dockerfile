FROM oven/bun:1 AS base

WORKDIR /app

# Install dependencies
COPY package.json bun.lock* ./
RUN bun install --production

# Copy source
COPY tsconfig.json ./
COPY src/ src/

# Expose WebSocket port (Render uses 10000 by default)
EXPOSE 10000

# Run the server
CMD ["bun", "run", "src/index.ts"]
