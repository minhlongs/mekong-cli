/**
 * License Activation Command
 * Activate beta invite license key with rate limiting and encryption
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';
import Redis from 'ioredis';
import {
  validateLicenseKeyFormat,
  extractTierFromKey,
  LicenseStore,
  activateLicenseKey,
  encryptLicenseKey,
} from '../lib/license-keys';
import { config } from '../config/env';

const ENV_PATH = join(process.cwd(), '.env');

// Rate limiting configuration
const RATE_LIMIT_MAX_ATTEMPTS = 5;
const RATE_LIMIT_WINDOW_MS = 60 * 60 * 1000; // 1 hour

/**
 * Get Redis client for rate limiting
 */
function getRedisClient(): Redis | null {
  try {
    const client = new Redis({
      host: config.REDIS_HOST,
      port: parseInt(config.REDIS_PORT, 10),
      password: config.REDIS_PASSWORD || undefined,
      retryStrategy: () => null, // Don't retry on failure
    });
    return client;
  } catch {
    return null;
  }
}

/**
 * Check rate limit for license activation
 * Returns true if allowed, false if exceeded
 */
async function checkRateLimit(identifier: string): Promise<{
  allowed: boolean;
  remaining: number;
  resetAt: number;
}> {
  const redis = getRedisClient();
  if (!redis) {
    // Redis unavailable - allow but log warning
    console.warn('⚠️  Redis unavailable - rate limiting disabled\n');
    return { allowed: true, remaining: RATE_LIMIT_MAX_ATTEMPTS, resetAt: 0 };
  }

  try {
    const key = `rate_limit:license_activation:${identifier}`;
    const now = Date.now();

    // Use Redis MULTI for atomic operations
    const multi = redis.multi();
    multi.zremrangebyscore(key, 0, now - RATE_LIMIT_WINDOW_MS);
    multi.zadd(key, now, `${now}-${Math.random()}`);
    multi.zcard(key);
    multi.expire(key, Math.ceil(RATE_LIMIT_WINDOW_MS / 1000));

    const results = await multi.exec();

    // Get count from ZCARD result (index 2)
    const count = results?.[3]?.[1] as number || 0;
    const remaining = Math.max(0, RATE_LIMIT_MAX_ATTEMPTS - count);
    const resetAt = now + RATE_LIMIT_WINDOW_MS;

    return {
      allowed: count < RATE_LIMIT_MAX_ATTEMPTS,
      remaining,
      resetAt,
    };
  } catch (error) {
    console.warn('⚠️  Rate limit check failed:', (error as Error).message);
    return { allowed: true, remaining: RATE_LIMIT_MAX_ATTEMPTS, resetAt: 0 };
  } finally {
    await redis.quit();
  }
}

/**
 * Record rate limit attempt
 */
async function recordRateLimitHit(identifier: string): Promise<void> {
  const redis = getRedisClient();
  if (!redis) return;

  try {
    const key = `rate_limit:license_activation:${identifier}`;
    const now = Date.now();
    await redis.zadd(key, now, `${now}-${Math.random()}`);
    await redis.expire(key, Math.ceil(RATE_LIMIT_WINDOW_MS / 1000));
  } catch {
    // Ignore errors - rate limiting is best-effort
  } finally {
    await redis.quit();
  }
}

/**
 * Get client identifier for rate limiting
 * Uses IP address or wallet address if available
 */
function getClientIdentifier(): string {
  // In CLI context, use a combination of hostname and timestamp
  // In server context, this would use IP or wallet
  const hostname = process.env.HOSTNAME || 'unknown';
  return `cli:${hostname}:${Date.now()}`;
}

export async function runActivateCommand(licenseKey?: string): Promise<void> {
  console.log('\n🔑 Algo Trader License Activation\n');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // Get license key from argument or prompt
  const key = licenseKey || await promptLicenseKey();

  if (!key) {
    console.log('❌ No license key provided.\n');
    console.log('Usage: algo-trader activate <your-license-key>');
    console.log('   or: algo-trader activate\n');
    return;
  }

  // Step 0: Check rate limit
  const clientId = getClientIdentifier();
  console.log('🔒 Checking activation rate limit...');
  const rateLimit = await checkRateLimit(clientId);

  if (!rateLimit.allowed) {
    const resetMinutes = Math.ceil((rateLimit.resetAt - Date.now()) / 60000);
    console.log(`❌ Rate limit exceeded. Maximum ${RATE_LIMIT_MAX_ATTEMPTS} activations per hour.\n`);
    console.log(`   Try again in ${resetMinutes} minutes.\n`);
    return;
  }

  if (rateLimit.remaining < RATE_LIMIT_MAX_ATTEMPTS) {
    console.log(`⚠️  ${rateLimit.remaining} activations remaining this hour\n`);
  } else {
    console.log('✅ Rate limit check passed\n');
  }

  // Step 1: Validate format
  console.log('📝 Validating license key format...');
  const validation = validateLicenseKeyFormat(key);

  if (!validation.valid) {
    await recordRateLimitHit(clientId);
    console.log(`❌ Invalid license key: ${validation.error}\n`);
    return;
  }
  console.log('✅ License key format valid\n');

  // Step 2: Extract tier
  const tier = extractTierFromKey(key);
  if (!tier) {
    await recordRateLimitHit(clientId);
    console.log('❌ Could not determine license tier\n');
    return;
  }
  console.log(`📊 License tier: ${tier.toUpperCase()}\n`);

  // Step 3: Store license (in production, this would call API)
  const store = LicenseStore.getInstance();

  // Check if already activated
  const existingLicense = store.getLicenseByKey(key);
  if (existingLicense) {
    if (existingLicense.status === 'active') {
      console.log('✅ License already activated!\n');
      console.log(`  Tier: ${existingLicense.tier.toUpperCase()}`);
      console.log(`  Usage: ${existingLicense.usageCount}/${existingLicense.maxUsage}`);
      if (existingLicense.expiresAt) {
        console.log(`  Expires: ${new Date(existingLicense.expiresAt).toLocaleDateString()}`);
      }
      console.log('');
      return;
    }

    if (existingLicense.status === 'revoked') {
      console.log('❌ This license has been revoked\n');
      return;
    }

    // Activate pending license
    activateLicenseKey(existingLicense);
    console.log('✅ License activated successfully!\n');
  } else {
    // Create new license entry
    const newLicense = {
      id: `lic_${Date.now()}`,
      key,
      tier,
      status: 'active' as const,
      createdAt: new Date().toISOString(),
      activatedAt: new Date().toISOString(),
      usageCount: 0,
      maxUsage: tier === 'free' ? 100 : tier === 'pro' ? 10000 : 100000,
    };
    store.saveLicense(newLicense);
    console.log('✅ License activated successfully!\n');
  }

  // Step 4: Encrypt and save to .env
  console.log('🔐 Encrypting license key for secure storage...');
  let encryptedKey: string;
  try {
    encryptedKey = encryptLicenseKey(key);
    console.log('✅ License key encrypted (AES-256-CBC)\n');
  } catch (error) {
    console.log(`❌ Encryption failed: ${(error as Error).message}\n`);
    console.log('💡 Make sure LICENSE_ENCRYPTION_KEY is set in your .env file\n');
    await recordRateLimitHit(clientId);
    return;
  }

  console.log('💾 Saving encrypted license key to configuration...');
  saveEncryptedLicenseToEnv(encryptedKey);
  console.log(`✅ Saved to: ${ENV_PATH}\n`);

  // Step 5: Show next steps
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🎉 ACTIVATION COMPLETE!');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('Next steps:');
  console.log('  1. Run `algo-trader quickstart` to start trading');
  console.log('  2. Access premium features with your tier');
  console.log('  3. Check usage: `algo-trader status`\n');

  if (tier === 'free') {
    console.log('⚠️  Free tier limit: 100 API calls/month');
    console.log('   Upgrade to Pro for unlimited trading\n');
  }
}

async function promptLicenseKey(): Promise<string> {
  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    readline.question('Enter your license key: ', (answer: string) => {
      readline.close();
      resolve(answer.trim());
    });
  });
}

/**
 * Save encrypted license key to .env file
 */
function saveEncryptedLicenseToEnv(encryptedKey: string): void {
  let envContent = '';

  if (existsSync(ENV_PATH)) {
    envContent = readFileSync(ENV_PATH, 'utf-8');

    // Remove existing LICENSE_KEY and LICENSE_KEY_ENCRYPTED if present
    const lines = envContent.split('\n');
    const filteredLines = lines.filter(
      (line) => !line.startsWith('LICENSE_KEY=') && !line.startsWith('LICENSE_KEY_ENCRYPTED=')
    );
    envContent = filteredLines.join('\n');

    // Ensure newline at end
    if (!envContent.endsWith('\n')) {
      envContent += '\n';
    }
  }

  // Add encrypted license key
  envContent += `\n# Encrypted License Key (activated ${new Date().toISOString()})
# Do not modify - this is your encrypted license key
LICENSE_KEY_ENCRYPTED=${encryptedKey}
`;

  writeFileSync(ENV_PATH, envContent);
}
