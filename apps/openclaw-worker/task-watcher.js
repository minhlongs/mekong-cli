#!/usr/bin/env node
/**
 * OpenClaw Task Watcher
 * Watches /tmp for openclaw_task_*.txt files and executes them via CC CLI
 */

const fs = require('fs');
const { exec, spawn } = require('child_process');
const path = require('path');

const WATCH_DIR = '/tmp';
const TASK_PATTERN = /^openclaw_task_.*\.txt$/;
const TELEGRAM_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '8405197398:AAHuuykECSxEGZaBZVhtvwyIWM84LtGLO5I';
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || '5503922921';
const PROCESSED_DIR = '/tmp/openclaw_processed';
const MEKONG_DIR = '/Users/macbookprom1/mekong-cli';

// Ensure processed dir exists
if (!fs.existsSync(PROCESSED_DIR)) {
  fs.mkdirSync(PROCESSED_DIR, { recursive: true });
}

// Send message to Telegram
async function sendTelegram(text) {
  const url = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`;

  console.log('🔍 DEBUG sendTelegram() called');
  console.log('   URL:', url);
  console.log('   Chat ID:', TELEGRAM_CHAT_ID);
  console.log('   Message preview:', text.slice(0, 100));

  try {
    const payload = {
      chat_id: TELEGRAM_CHAT_ID,
      text: text,
      parse_mode: 'Markdown'
    };

    console.log('   Payload:', JSON.stringify(payload, null, 2));

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const responseData = await response.json();

    if (!response.ok) {
      console.error('❌ Telegram API error:', {
        status: response.status,
        statusText: response.statusText,
        data: responseData
      });
      throw new Error(`Telegram API returned ${response.status}: ${JSON.stringify(responseData)}`);
    }

    console.log('✅ Telegram sent successfully!');
    console.log('   Response:', JSON.stringify(responseData, null, 2));

  } catch (error) {
    console.error('❌ sendTelegram() FAILED:');
    console.error('   Error name:', error.name);
    console.error('   Error message:', error.message);
    console.error('   Error stack:', error.stack);
    throw error; // Re-throw to let caller know it failed
  }
}

// Execute task via CC CLI
function executeTask(taskContent, taskFile) {
  return new Promise((resolve) => {
    // Remove backslash escapes from Telegram (e.g., \! -> !)
    const cleanContent = taskContent.replace(/\\!/g, '!').replace(/\\"/g, '"');
    console.log(`\n📋 Original: ${taskContent.slice(0, 50)}...`);
    console.log(`📋 Cleaned: ${cleanContent.slice(0, 50)}...`);

    // For shell commands (prefix !)
    if (cleanContent.startsWith('!')) {
      const cmd = cleanContent.slice(1);
      console.log(`🔧 Executing shell: ${cmd}`);

      const { exec } = require('child_process');
      exec(cmd, { cwd: MEKONG_DIR }, (error, stdout, stderr) => {
        const result = {
          success: !error,
          output: stdout || stderr || error?.message || 'No output'
        };
        console.log(`📊 Shell completed:`, { success: result.success });
        resolve(result);
      });
      return;
    }

    // For Claude tasks - spawn CC CLI with task
    console.log(`🤖 Executing Claude task: ${cleanContent}`);
    const claude = spawn('claude', ['-p', cleanContent], {
      cwd: MEKONG_DIR,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, PATH: '/opt/homebrew/bin:/usr/local/bin:' + process.env.PATH }
    });

    let output = '';
    let errorOutput = '';

    claude.stdout.on('data', (data) => {
      const text = data.toString();
      output += text;
      console.log(text);
    });

    claude.stderr.on('data', (data) => {
      const text = data.toString();
      errorOutput += text;
      console.error(text);
    });

    claude.on('close', (code) => {
      const fullOutput = output + errorOutput;
      resolve({
        success: code === 0,
        output: fullOutput.slice(-3000) || 'Task completed with no output'
      });
    });

    claude.on('error', (error) => {
      resolve({
        success: false,
        output: `Failed to start claude: ${error.message}`
      });
    });

    // Timeout after 5 minutes
    setTimeout(() => {
      claude.kill();
      resolve({
        success: false,
        output: 'Timeout after 5 minutes'
      });
    }, 5 * 60 * 1000);
  });
}

// Process new task file
async function processTask(taskFile) {
  const filePath = path.join(WATCH_DIR, taskFile);

  try {
    // Wait a bit for file to be fully written
    await new Promise(resolve => setTimeout(resolve, 500));

    const content = fs.readFileSync(filePath, 'utf-8').trim();
    console.log(`\n🔔 New task: ${taskFile}`);
    console.log(`📝 Task content: "${content}"`);

    // Send initial notification
    try {
      console.log('\n📤 Sending initial Telegram notification...');
      await sendTelegram(`⏳ Processing task...\n\n"${content.slice(0, 200)}"`);
      console.log('✅ Initial notification sent!');
    } catch (telegramError) {
      console.error('❌ Failed to send initial notification:', telegramError.message);
      // Continue anyway
    }

    // Execute the task
    console.log('\n🚀 Executing task...');
    const result = await executeTask(content, taskFile);
    console.log('\n📊 Task execution result:', {
      success: result.success,
      outputLength: result.output.length
    });

    // Send result notification
    try {
      const status = result.success ? '✅ SUCCESS' : '❌ FAILED';
      const message = `${status}\n\n${result.output.slice(0, 3500)}`;

      console.log('\n📤 Sending result Telegram notification...');
      console.log('   Status:', status);
      console.log('   Message length:', message.length);

      await sendTelegram(message);
      console.log('✅ Result notification sent!');
    } catch (telegramError) {
      console.error('❌ Failed to send result notification:', telegramError.message);
      // Continue to move file anyway
    }

    // Move to processed
    const processedPath = path.join(PROCESSED_DIR, taskFile);
    fs.renameSync(filePath, processedPath);
    console.log(`\n✅ Task completed and moved: ${taskFile}`);

  } catch (error) {
    console.error('\n❌ Task processing error:', error);
    console.error('   Error name:', error.name);
    console.error('   Error message:', error.message);
    console.error('   Error stack:', error.stack);

    try {
      console.log('\n📤 Sending error notification to Telegram...');
      await sendTelegram(`❌ Error processing task: ${error.message}`);
      console.log('✅ Error notification sent!');
    } catch (telegramError) {
      console.error('❌ Failed to send error notification:', telegramError.message);
    }

    // Still move to processed to avoid reprocessing
    try {
      const processedPath = path.join(PROCESSED_DIR, `error_${taskFile}`);
      fs.renameSync(filePath, processedPath);
      console.log(`📦 Error file moved: ${processedPath}`);
    } catch (e) {
      console.error('❌ Failed to move error file:', e);
    }
  }
}

// Track processed files to avoid duplicates
const processedFiles = new Set();

// Watch for new files
console.log('👀 Watching for Telegram tasks...');
console.log(`📁 Directory: ${WATCH_DIR}`);
console.log(`🎯 Pattern: ${TASK_PATTERN}`);
console.log(`📦 Processed dir: ${PROCESSED_DIR}`);

fs.watch(WATCH_DIR, (eventType, filename) => {
  if (eventType === 'rename' && filename && TASK_PATTERN.test(filename)) {
    const filePath = path.join(WATCH_DIR, filename);

    // Check if file exists (rename event fires on both create and delete)
    if (fs.existsSync(filePath) && !processedFiles.has(filename)) {
      processedFiles.add(filename);
      processTask(filename).finally(() => {
        // Remove from set after processing
        setTimeout(() => processedFiles.delete(filename), 60000);
      });
    }
  }
});

// Initial scan for existing files
console.log('🔍 Scanning for existing task files...');
const existingFiles = fs.readdirSync(WATCH_DIR)
  .filter(f => TASK_PATTERN.test(f));

if (existingFiles.length > 0) {
  console.log(`Found ${existingFiles.length} existing task(s)`);
  existingFiles.forEach(f => {
    processedFiles.add(f);
    processTask(f).finally(() => {
      setTimeout(() => processedFiles.delete(f), 60000);
    });
  });
} else {
  console.log('No existing tasks found');
}

console.log('✅ Task watcher ready!\n');

// Startup notification DISABLED to prevent spam

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n⏹️  Shutting down task watcher...');
  // Notification DISABLED to prevent spam
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n⏹️  Shutting down task watcher...');
  // Notification DISABLED to prevent spam
  process.exit(0);
});
