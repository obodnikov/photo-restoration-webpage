# Multi-stage build for React frontend

# Build stage
FROM node:22.12-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables
# These are available during build time only
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_APP_NAME="Photo Restoration"
ARG VITE_APP_VERSION="1.0.0"

# Set as environment variables for the build process
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_APP_NAME=${VITE_APP_NAME}
ENV VITE_APP_VERSION=${VITE_APP_VERSION}

# Build the application
# Vite will embed these environment variables into the build
RUN npm run build

# Production stage - serve with simple static file server
FROM node:22.12-alpine

# Install serve package globally
RUN npm install -g serve

# Create app directory
WORKDIR /app

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start serve (SPA mode handles React Router)
CMD ["serve", "-s", "dist", "-l", "3000"]
