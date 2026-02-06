import 'dotenv/config';
import prisma from './db.js';
import './worker.js';

async function cleanupStaleJobs() {
  console.log('🧹 Checking for stale jobs...');
  try {
    const { count } = await prisma.job.updateMany({
      where: {
        status: 'PROCESSING',
      },
      data: {
        status: 'FAILED',
        error: 'Worker crashed or restarted while processing',
        completedAt: new Date(),
      },
    });

    if (count > 0) {
      console.log(`⚠️  Reset ${count} stale jobs to FAILED status`);
    } else {
      console.log('✨ No stale jobs found');
    }
  } catch (error) {
    console.error('❌ Failed to clean up stale jobs:', error);
  }
}

// Run cleanup on startup
cleanupStaleJobs().catch(console.error);

console.log('🚀 Agency Worker Service Started');
console.log('👀 Listening for jobs in queue: agency-queue');

// Keep process alive
process.on('SIGINT', () => {
  console.log('Shutting down...');
  process.exit(0);
});
