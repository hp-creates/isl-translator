# ---- Build Stage ----
FROM node:20-alpine AS builder

WORKDIR /build

# Copy dependency files first (layer caching)
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY . .

# Build for production
RUN npm run build

# ---- Production Stage ----
FROM nginx:alpine AS production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static files
COPY --from=builder /build/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Nginx runs as non-root in alpine by default
CMD ["nginx", "-g", "daemon off;"]
