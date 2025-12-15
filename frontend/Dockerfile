# ===========
# 1) Build stage (React + Vite)
# ===========
FROM node:22.12-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build production bundle (Vite)
RUN npm run build

# ===========
# 2) Runtime stage (Nginx serving static files)
# ===========
FROM nginx:1.27-alpine

# Remove default config (optional but cleaner)
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Health check (simple HTTP GET on root)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1
