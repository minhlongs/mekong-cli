# Use official Node.js LTS image
FROM node:20-alpine

# Install OpenSSL for Prisma
RUN apk add --no-cache openssl

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies (including devDependencies for prisma generate)
RUN npm install

# Copy Prisma schema and config
COPY prisma ./prisma

# Copy source code
COPY src ./src

# Generate Prisma Client
RUN npx prisma generate

# Start the service
CMD ["npm", "start"]
