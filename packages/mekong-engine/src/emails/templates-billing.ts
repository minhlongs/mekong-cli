/**
 * Tutorial & Usage Milestone Email Templates
 */

import type { EmailTemplate, TutorialEmailData, MilestoneEmailData } from './templates-types'

export function createTutorialEmail(data: TutorialEmailData): EmailTemplate {
  const subject = `Step ${data.tutorialStep}/${data.totalSteps}: Your first command awaits!`

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #11998e, #38ef7d); color: white; padding: 20px; border-radius: 10px 10px 0 0; }
    .progress { background: #e0e0e0; height: 8px; border-radius: 4px; margin: 20px 0; overflow: hidden; }
    .progress-bar { background: linear-gradient(90deg, #11998e, #38ef7d); height: 100%; width: ${((data.tutorialStep - 1) / (data.totalSteps - 1)) * 100}%; transition: width 0.3s; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    .button { display: inline-block; background: #11998e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; }
    .tip { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }
    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="header">
    <h2>📍 Step ${data.tutorialStep} of ${data.totalSteps}</h2>
    <p>You're making great progress!</p>
  </div>
  <div class="content">
    <div class="progress">
      <div class="progress-bar"></div>
    </div>
    <h3>Ready for the next step?</h3>
    <p>Hi ${data.tenantName},</p>
    <p>You're ${Math.round(((data.tutorialStep - 1) / (data.totalSteps - 1)) * 100)}% through the onboarding tutorial. Let's continue with step ${data.tutorialStep}!</p>
    <div class="tip">
      <strong>💡 Pro tip:</strong> Each step takes about 2-3 minutes. You've got this!
    </div>
    <p style="text-align: center; margin-top: 25px;">
      <a href="${data.tutorialUrl}" class="button">Continue Tutorial</a>
    </p>
  </div>
  <div class="footer">
    <p>Mekong RaaS - AI-operated business platform</p>
  </div>
</body>
</html>
`.trim()

  const text = `
Step ${data.tutorialStep}/${data.totalSteps}: Your first command awaits!

Hi ${data.tenantName},

You're ${Math.round(((data.tutorialStep - 1) / (data.totalSteps - 1)) * 100)}% through the onboarding tutorial. Let's continue with step ${data.tutorialStep}!

💡 Pro tip: Each step takes about 2-3 minutes. You've got this!

Continue here: ${data.tutorialUrl}

--
Mekong RaaS
  `.trim()

  return { subject, html, text }
}

export function createMilestoneEmail(data: MilestoneEmailData): EmailTemplate {
  const isUpgradePrompt = data.usagePercent >= 80
  const isComplete = data.usagePercent >= 100

  const emoji = isComplete ? '🎉' : isUpgradePrompt ? '⚠️' : data.usagePercent >= 50 ? '📈' : '🚀'
  const title = isComplete ? 'Tier Complete!' : isUpgradePrompt ? 'Almost at your limit!' : 'Usage Milestone'

  const subject = isComplete
    ? `🎉 You've reached your ${data.tierName} tier limit!`
    : isUpgradePrompt
      ? `⚠️ ${data.usagePercent}% used - Time to upgrade?`
      : `📊 You've used ${data.usagePercent}% of your ${data.tierName} credits`

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: ${isComplete ? 'linear-gradient(135deg, #f093fb, #f5576c)' : isUpgradePrompt ? 'linear-gradient(135deg, #ff9966, #ff5e62)' : 'linear-gradient(135deg, #56ab2f, #a8e063)'}; color: white; padding: 25px; border-radius: 10px 10px 0 0; text-align: center; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    .meter { background: #e0e0e0; height: 20px; border-radius: 10px; margin: 20px 0; overflow: hidden; position: relative; }
    .meter-fill { background: ${isComplete ? '#f5576c' : isUpgradePrompt ? '#ff5e62' : '#56ab2f'}; height: 100%; width: ${Math.min(data.usagePercent, 100)}%; transition: width 0.3s; }
    .meter-text { position: absolute; width: 100%; text-align: center; top: 0; font-size: 12px; font-weight: bold; color: ${data.usagePercent > 50 ? 'white' : '#333'}; }
    .stats { display: flex; justify-content: space-around; margin: 20px 0; }
    .stat { text-align: center; padding: 15px; background: white; border-radius: 8px; flex: 1; margin: 0 5px; }
    .stat-value { font-size: 24px; font-weight: bold; color: #667eea; }
    .stat-label { font-size: 12px; color: #666; }
    .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
    .button.secondary { background: #f0f0f0; color: #333; }
    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>${emoji} ${title}</h1>
    ${isComplete ? '<p>Congratulations on maximizing your tier!</p>' : ''}
  </div>
  <div class="content">
    <p>Hi ${data.tenantName},</p>
    <p>You've used <strong>${data.usagePercent}%</strong> of your ${data.tierName} tier credits.</p>
    <div class="meter">
      <div class="meter-fill"></div>
      <div class="meter-text">${data.currentUsage} / ${data.tierLimit} credits</div>
    </div>
    <div class="stats">
      <div class="stat">
        <div class="stat-value">${data.currentUsage.toLocaleString()}</div>
        <div class="stat-label">Credits Used</div>
      </div>
      <div class="stat">
        <div class="stat-value">${(data.tierLimit - data.currentUsage).toLocaleString()}</div>
        <div class="stat-label">Credits Remaining</div>
      </div>
    </div>
    ${isUpgradePrompt ? `
      <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0;">
        <strong>💡 Suggestion:</strong> Consider upgrading to the next tier to avoid service interruption and unlock more features!
      </div>
    ` : ''}
    ${isComplete ? `
      <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0;">
        <strong>🎉 Great job!</strong> You've fully utilized your ${data.tierName} tier. Upgrade now to continue with uninterrupted service.
      </div>
    ` : ''}
    <p style="text-align: center; margin-top: 25px;">
      ${isUpgradePrompt || isComplete ? `<a href="${data.upgradeUrl}" class="button">Upgrade Now</a>` : ''}
      <a href="/v1/reports/usage" class="button secondary">View Detailed Usage</a>
    </p>
  </div>
  <div class="footer">
    <p>Mekong RaaS - AI-operated business platform</p>
  </div>
</body>
</html>
`.trim()

  const text = `
${title}

Hi ${data.tenantName},

You've used ${data.usagePercent}% of your ${data.tierName} tier credits.

USAGE: ${data.currentUsage} / ${data.tierLimit} credits
REMAINING: ${(data.tierLimit - data.currentUsage).toLocaleString()} credits

${isUpgradePrompt ? '\n💡 SUGGESTION: Consider upgrading to the next tier to avoid service interruption!\n' : ''}
${isComplete ? '\n🎉 You\'ve fully utilized your tier. Upgrade now to continue!\n' : ''}

${isUpgradePrompt || isComplete ? `Upgrade: ${data.upgradeUrl}\n` : ''}
View detailed usage: /v1/reports/usage

--
Mekong RaaS
  `.trim()

  return { subject, html, text }
}
