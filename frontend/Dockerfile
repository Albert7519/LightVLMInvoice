# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE=/api/v1/invoices
ENV VITE_API_BASE=$VITE_API_BASE

# Run TypeScript and Vite builds directly to avoid permission issues with bin stubs
RUN node ./node_modules/typescript/bin/tsc -b && \
  node ./node_modules/vite/bin/vite.js build

# Stage 2: Serve
FROM nginx:1.25-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget -q -O- http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
