FROM oven/bun:1 AS base

WORKDIR /app

# Install dependencies
COPY package.json bun.lock* ./
RUN bun install --production

# Copy source
COPY tsconfig.json ./
COPY src/ src/

# Expose port (set via PORT env var, Fly.io uses 8080)
EXPOSE 8080

# Run the server
CMD ["bun", "run", "src/index.ts"]
