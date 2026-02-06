import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { PrismaClient } = require('@prisma/client');

console.log('Initializing Prisma Client (Standard)...');
console.log('DATABASE_URL present:', !!process.env.DATABASE_URL);

let prisma;
try {
  prisma = new PrismaClient();
  console.log('Prisma Client initialized successfully');
} catch (error) {
  console.error('Failed to initialize Prisma Client:', error);
  throw error;
}

export default prisma;
