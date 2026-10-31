# Dockerfile for Jenna AI Assistant Next.js Frontend
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY frontend/package.json ./
RUN npm install

# Copy application files
COPY frontend/ ./

ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

EXPOSE 3000

CMD ["npm", "run", "dev"]
