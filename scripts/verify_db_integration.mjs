import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { PrismaClient } = require('../apps/engine/node_modules/@prisma/client');

const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL || 'postgresql://postgres:password@localhost:5432/agency_os?schema=public',
    },
  },
});

async function verify() {
  console.log('🔍 Verifying Database State...');

  // 1. Check if we can connect
  try {
    await prisma.$connect();
    console.log('✅ Connected to Database');
  } catch (error) {
    console.error('❌ Failed to connect to database:', error);
    process.exit(1);
  }

  // 2. Look for recent jobs
  const jobs = await prisma.job.findMany({
    orderBy: { createdAt: 'desc' },
    take: 5,
  });

  if (jobs.length === 0) {
    console.log('⚠️ No jobs found in database. Did you send a request?');
    process.exit(1);
  }

  console.log(`found ${jobs.length} jobs.`);

  const latestJob = jobs[0];
  console.log('Latest Job:', JSON.stringify(latestJob, null, 2));

  // 3. Verify specific fields
  if (latestJob.type !== 'chat.completion') {
    console.error('❌ Job type mismatch');
    process.exit(1);
  }

  if (['COMPLETED', 'FAILED'].includes(latestJob.status)) {
    console.log(`✅ Job Status is ${latestJob.status}`);
    if (latestJob.status === 'COMPLETED' && latestJob.output) {
        console.log('✅ Job has output');
    } else if (latestJob.status === 'FAILED' && latestJob.error) {
        console.log('✅ Job has error');
    }
  } else {
    console.log(`ℹ️ Job Status is ${latestJob.status} (Worker might still be processing)`);
  }

  await prisma.$disconnect();
}

verify();
