FROM oven/bun:1 AS base

WORKDIR /app

# Install dependencies
COPY package.json bun.lock* ./
RUN bun install --production

# Copy source
COPY tsconfig.json ./
COPY src/ src/

# Expose port (set via PORT env var in fly.toml)
EXPOSE 433

# Run the server
CMD ["bun", "run", "src/index.ts"]
