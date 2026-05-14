FROM node:22-slim AS builder

WORKDIR /frontend

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build:docker

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /frontend/dist /usr/share/nginx/html

EXPOSE 80
