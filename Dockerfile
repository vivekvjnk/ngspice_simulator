FROM node:20-slim

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY tsconfig.json ./
COPY src ./src

RUN pnpm build

# Create directory for library volume
RUN mkdir -p /app/lib

# Environment variables
ENV VHL_TRANSPORT=http
ENV PORT=8080
ENV VHL_LIBRARY_DIR=/app/lib

# Expose port
EXPOSE 8080

# Define volume for persistent library storage
VOLUME ["/app/lib"]

CMD ["node", "dist/index.js"]
