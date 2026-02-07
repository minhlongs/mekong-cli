/**
 * 🏦 Polar Balance Checker & Auto-Notify
 * 
 * Checks Polar.sh balance and sends notification when ready for withdrawal.
 * Setup as cron job for automatic monitoring.
 * 
 * Usage:
 *   npx ts-node scripts/polar-balance-checker.ts
 *   
 * Cron (check every 6 hours):
 *   0 * / 6 * * * cd ~/mekong-cli && npx ts-node scripts/polar-balance-checker.ts
 */

// Configuration
const CONFIG = {
  // Minimum balance (USD) to trigger notification
  MIN_WITHDRAWAL_AMOUNT: 100,
  
  // Bank details for reference
  BANK: {
    name: 'ACB (Asia Commercial Bank)',
    accountNumber: '5566776868',
    accountHolder: 'TRẦN THIỆN LÂM',
    branch: 'ACB Đồng Tháp',
    citid: '87307001',
  },
  
  // Notification settings
  TELEGRAM_BOT_TOKEN: process.env.TELEGRAM_BOT_TOKEN || '',
  TELEGRAM_CHAT_ID: process.env.TELEGRAM_CHAT_ID || '',
  
  // Polar API
  POLAR_API_URL: 'https://api.polar.sh/v1',
};

interface PolarOrg {
  id: string;
  name: string;
}

interface PolarTransaction {
  type: string;
  amount?: number;
}

async function checkPolarBalance(): Promise<void> {
  const accessToken = process.env.POLAR_ACCESS_TOKEN;
  
  if (!accessToken) {
    console.error('❌ POLAR_ACCESS_TOKEN not set');
    process.exit(1);
  }
  
  const headers = {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  };
  
  try {
    console.log('🔍 Checking Polar.sh balance...\n');
    
    // Get organization info
    const orgsResponse = await fetch(`${CONFIG.POLAR_API_URL}/organizations`, {
      headers,
    });
    
    if (!orgsResponse.ok) {
      throw new Error(`Failed to fetch orgs: ${orgsResponse.status}`);
    }
    
    const orgsData = await orgsResponse.json() as { items?: PolarOrg[] };
    
    if (!orgsData.items?.length) {
      console.log('⚠️ No organizations found');
      return;
    }
    
    const org = orgsData.items[0];
    console.log(`📊 Organization: ${org.name}`);
    
    // Get transactions
    const txResponse = await fetch(
      `${CONFIG.POLAR_API_URL}/transactions?organization_id=${org.id}`,
      { headers }
    );
    
    if (!txResponse.ok) {
      console.log('⚠️ Could not fetch transactions, checking account balance...');
    }
    
    const txData = await txResponse.json() as { items?: PolarTransaction[] };
    
    // Calculate available balance
    let totalBalance = 0;
    
    if (txData.items) {
      for (const tx of txData.items) {
        if (tx.type === 'payment' && tx.amount) {
          totalBalance += tx.amount;
        } else if (tx.type === 'payout' && tx.amount) {
          totalBalance -= tx.amount;
        }
      }
    }
    
    // Convert cents to dollars
    const balanceUSD = totalBalance / 100;
    
    console.log(`\n💰 Current Balance: $${balanceUSD.toFixed(2)} USD`);
    console.log(`📋 Min Withdrawal: $${CONFIG.MIN_WITHDRAWAL_AMOUNT} USD`);
    
    if (balanceUSD >= CONFIG.MIN_WITHDRAWAL_AMOUNT) {
      console.log('\n✅ READY FOR WITHDRAWAL!');
      console.log('\n📤 Payout Details:');
      console.log(`   Bank: ${CONFIG.BANK.name}`);
      console.log(`   Account: ${CONFIG.BANK.accountNumber}`);
      console.log(`   Name: ${CONFIG.BANK.accountHolder}`);
      console.log(`   Branch: ${CONFIG.BANK.branch}`);
      
      // Send Telegram notification if configured
      await sendTelegramNotification(balanceUSD);
      
      console.log('\n🔗 Withdraw at: https://polar.sh/dashboard/finance');
    } else {
      const remaining = CONFIG.MIN_WITHDRAWAL_AMOUNT - balanceUSD;
      console.log(`\n⏳ Need $${remaining.toFixed(2)} more to reach withdrawal threshold`);
    }
    
  } catch (error) {
    console.error('❌ Error checking balance:', error);
  }
}

async function sendTelegramNotification(balance: number): Promise<void> {
  if (!CONFIG.TELEGRAM_BOT_TOKEN || !CONFIG.TELEGRAM_CHAT_ID) {
    console.log('ℹ️ Telegram not configured, skipping notification');
    return;
  }
  
  const message = `
🏦 *Polar.sh Balance Alert*

💰 Balance: *$${balance.toFixed(2)} USD*
✅ Ready for withdrawal!

📤 *Payout to:*
• Bank: ACB
• Account: 5566776868  
• Name: TRẦN THIỆN LÂM

🔗 [Withdraw Now](https://polar.sh/dashboard/finance)
  `.trim();
  
  try {
    const response = await fetch(
      `https://api.telegram.org/bot${CONFIG.TELEGRAM_BOT_TOKEN}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: CONFIG.TELEGRAM_CHAT_ID,
          text: message,
          parse_mode: 'Markdown',
        }),
      }
    );
    
    if (response.ok) {
      console.log('📱 Telegram notification sent!');
    }
  } catch (error) {
    console.error('Failed to send Telegram notification:', error);
  }
}

// Run
checkPolarBalance();
