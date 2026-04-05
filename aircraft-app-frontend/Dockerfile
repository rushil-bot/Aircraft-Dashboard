# ---- Frontend Dockerfile ----
# Multi-stage build: Node builds React app, Nginx serves it

# Stage 1: Build the React application (use full Node, not Alpine, for native deps)
FROM node:20 AS builder

WORKDIR /app

# Install dependencies first (layer caching)
COPY package.json package-lock.json ./
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx (Alpine is fine here — just static files)
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built React app from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
