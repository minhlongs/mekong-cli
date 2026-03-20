/**
 * Email Templates for Beta Onboarding Flow
 * Supports: Welcome, Verification, Milestone, Feedback, NPS surveys
 */

export interface EmailTemplate {
  subject: string
  html: string
  text: string
}

export interface WelcomeEmailData {
  tenantName: string
  businessName: string
  apiKey: string
  dashboardUrl: string
  docsUrl: string
}

export interface VerificationEmailData {
  email: string
  verificationCode: string
  verificationUrl: string
}

export interface TutorialEmailData {
  tenantName: string
  tutorialStep: number
  totalSteps: number
  tutorialUrl: string
}

export interface MilestoneEmailData {
  tenantName: string
  usagePercent: number
  currentUsage: number
  tierLimit: number
  tierName: string
  upgradeUrl: string
}

export interface FeedbackEmailData {
  tenantName: string
  feedbackUrl: string
  npsSurveyUrl: string
}

/**
 * Welcome Email - sent after successful signup
 */
export function createWelcomeEmail(data: WelcomeEmailData): EmailTemplate {
  const subject = `Welcome to Mekong RaaS, ${data.businessName}!`

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 10px 0; }
    .code-block { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; font-family: 'Monaco', 'Consolas', monospace; word-break: break-all; }
    .steps { background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }
    .step { margin: 15px 0; padding-left: 10px; border-left: 3px solid #667eea; }
    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>👋 Welcome to Mekong RaaS!</h1>
    <p>Your AI-powered business platform is ready</p>
  </div>

  <div class="content">
    <p>Hi <strong>${data.tenantName}</strong>,</p>

    <p>Thanks for joining the Mekong RaaS beta! Your account for <strong>${data.businessName}</strong> has been successfully created.</p>

    <div class="steps">
      <h3>🚀 Get Started in 3 Steps:</h3>
      <div class="step">
        <strong>1. Save your API key</strong><br>
        <div class="code-block">${data.apiKey}</div>
        <small>⚠️ Store this securely - you won't see it again!</small>
      </div>
      <div class="step">
        <strong>2. Complete the onboarding wizard</strong><br>
        Set up your business profile, connect channels, and configure your first command.
      </div>
      <div class="step">
        <strong>3. Run your first command</strong><br>
        Try <code>/cook</code> to build your first feature in minutes.
      </div>
    </div>

    <p style="text-align: center;">
      <a href="${data.dashboardUrl}" class="button">Open Dashboard</a>
    </p>

    <h4>📚 Resources:</h4>
    <ul>
      <li><a href="${data.docsUrl}">Documentation & Quickstart Guide</a></li>
      <li><a href="https://docs.agencyos.network/guides/commands">Command Reference</a></li>
      <li><a href="https://discord.gg/mekong">Join our Discord community</a></li>
    </ul>

    <p>Need help? Reply to this email or join our Discord. We're here to help you succeed! 🙌</p>
  </div>

  <div class="footer">
    <p>Mekong RaaS - AI-operated business platform</p>
    <p>Questions? Contact us at hello@agencyos.network</p>
  </div>
</body>
</html>
`.trim()

  const text = `
Welcome to Mekong RaaS!

Hi ${data.tenantName},

Thanks for joining the Mekong RaaS beta! Your account for ${data.businessName} has been successfully created.

🚀 GET STARTED IN 3 STEPS:

1. SAVE YOUR API KEY
${data.apiKey}
⚠️ Store this securely - you won't see it again!

2. COMPLETE THE ONBOARDING WIZARD
Set up your business profile, connect channels, and configure your first command.

3. RUN YOUR FIRST COMMAND
Try /cook to build your first feature in minutes.

Open Dashboard: ${data.dashboardUrl}

📚 RESOURCES:
- Documentation: ${data.docsUrl}
- Command Reference: https://docs.agencyos.network/guides/commands
- Discord: https://discord.gg/mekong

Need help? Reply to this email or join our Discord!

--
Mekong RaaS - AI-operated business platform
  `.trim()

  return { subject, html, text }
}

/**
 * Email Verification Code - sent during signup
 */
export function createVerificationEmail(data: VerificationEmailData): EmailTemplate {
  const subject = 'Verify your email address'

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: #667eea; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    .code { font-size: 32px; font-weight: bold; letter-spacing: 5px; text-align: center; padding: 20px; background: white; border: 2px dashed #667eea; border-radius: 10px; margin: 20px 0; }
    .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; }
    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>🔐 Verify Your Email</h1>
  </div>

  <div class="content">
    <p>Hi,</p>
    <p>Thanks for signing up! Please verify your email address by entering the code below:</p>

    <div class="code">${data.verificationCode}</div>

    <p style="text-align: center;">
      <a href="${data.verificationUrl}" class="button">Or click here to verify</a>
    </p>

    <p><small>This code expires in 15 minutes. If you didn't request this, please ignore this email.</small></p>
  </div>

  <div class="footer">
    <p>Mekong RaaS - AI-operated business platform</p>
  </div>
</body>
</html>
`.trim()

  const text = `
Verify Your Email

Hi,

Thanks for signing up! Please verify your email address by entering the code below:

${data.verificationCode}

Or visit: ${data.verificationUrl}

This code expires in 15 minutes. If you didn't request this, please ignore this email.

--
Mekong RaaS
  `.trim()

  return { subject, html, text }
}

/**
 * Tutorial Step Email - sent during first command walkthrough
 */
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

/**
 * Usage Milestone Email - sent at 10%, 50%, 80%, 100% of tier limit
 */
export function createMilestoneEmail(data: MilestoneEmailData): EmailTemplate {
  const isUpgradePrompt = data.usagePercent >= 80
  const isComplete = data.usagePercent >= 100

  let emoji = isComplete ? '🎉' : isUpgradePrompt ? '⚠️' : data.usagePercent >= 50 ? '📈' : '🚀'
  let title = isComplete ? 'Tier Complete!' : isUpgradePrompt ? 'Almost at your limit!' : 'Usage Milestone'

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
      ${isUpgradePrompt || isComplete ? `
        <a href="${data.upgradeUrl}" class="button">Upgrade Now</a>
      ` : ''}
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

/**
 * Feedback Request Email - sent after onboarding completion
 */
export function createFeedbackEmail(data: FeedbackEmailData): EmailTemplate {
  const subject = 'How was your onboarding experience?'

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px; border-radius: 10px 10px 0 0; text-align: center; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    .nps-scale { display: flex; justify-content: space-between; margin: 20px 0; }
    .nps-item { width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: 2px solid #667eea; border-radius: 5px; color: #667eea; font-weight: bold; text-decoration: none; }
    .nps-item:hover { background: #667eea; color: white; }
    .nps-labels { display: flex; justify-content: space-between; margin-top: 10px; font-size: 12px; color: #666; }
    .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
    .feedback-box { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e0e0e0; }
    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>💬 We'd love your feedback!</h1>
    <p>Help us improve Mekong RaaS</p>
  </div>

  <div class="content">
    <p>Hi ${data.tenantName},</p>
    <p>Now that you've completed onboarding, we'd appreciate your feedback. How likely are you to recommend Mekong RaaS to a friend or colleague?</p>

    <div class="feedback-box">
      <h4 style="margin-top: 0;">NPS Score</h4>
      <p style="font-size: 14px; color: #666;">0 = Not at all likely, 10 = Extremely likely</p>
      <div class="nps-scale">
        ${[0,1,2,3,4,5,6,7,8,9,10].map(i =>
          `<a href="${data.npsSurveyUrl}?score=${i}" class="nps-item">${i}</a>`
        ).join('')}
      </div>
      <div class="nps-labels">
        <span>Not likely</span>
        <span>Extremely likely</span>
      </div>
    </div>

    <h4>Have feature requests or feedback?</h4>
    <p>We're constantly improving Mekong RaaS based on user input. Share your thoughts:</p>

    <p style="text-align: center;">
      <a href="${data.feedbackUrl}" class="button">Submit Feedback</a>
    </p>

    <p><small>Your feedback helps shape the future of Mekong RaaS. Thank you! 🙏</small></p>
  </div>

  <div class="footer">
    <p>Mekong RaaS - AI-operated business platform</p>
  </div>
</body>
</html>
`.trim()

  const text = `
We'd love your feedback!

Hi ${data.tenantName},

Now that you've completed onboarding, we'd appreciate your feedback. How likely are you to recommend Mekong RaaS to a friend or colleague?

NPS SCORE (0 = Not at all likely, 10 = Extremely likely):
${data.npsSurveyUrl}

HAVE FEATURE REQUESTS OR FEEDBACK?
Submit here: ${data.feedbackUrl}

Your feedback helps shape the future of Mekong RaaS. Thank you!

--
Mekong RaaS
  `.trim()

  return { subject, html, text }
}

/**
 * Account Setup Wizard Email - sent when signup is incomplete after 24h
 */
export function createSetupReminderEmail(data: { tenantName: string; businessName: string; setupUrl: string }): EmailTemplate {
  const subject = `Complete your ${data.businessName} setup`

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #f093fb, #f5576c); color: white; padding: 25px; border-radius: 10px 10px 0 0; text-align: center; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    .checklist { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .checklist-item { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
    .checklist-item:last-child { border-bottom: none; }
    .button { display: inline-block; background: #f5576c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; }
    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>📋 Finish Your Setup</h1>
    <p>Your account is waiting!</p>
  </div>

  <div class="content">
    <p>Hi ${data.tenantName},</p>
    <p>We noticed you haven't completed your ${data.businessName} account setup yet. It only takes 5 minutes!</p>

    <div class="checklist">
      <h4 style="margin-top: 0;">Quick Setup Checklist:</h4>
      <div class="checklist-item">✅ Account created</div>
      <div class="checklist-item">⏳ Business profile</div>
      <div class="checklist-item">⏳ Connect first channel</div>
      <div class="checklist-item">⏳ Run first command</div>
    </div>

    <p style="text-align: center;">
      <a href="${data.setupUrl}" class="button">Complete Setup (5 min)</a>
    </p>

    <p><small>Need help? Check our <a href="https://docs.agencyos.network/guides/quickstart">Quick Start Guide</a></small></p>
  </div>

  <div class="footer">
    <p>Mekong RaaS - AI-operated business platform</p>
  </div>
</body>
</html>
`.trim()

  const text = `
Finish Your Setup

Hi ${data.tenantName},

We noticed you haven't completed your ${data.businessName} account setup yet. It only takes 5 minutes!

QUICK SETUP CHECKLIST:
✅ Account created
⏳ Business profile
⏳ Connect first channel
⏳ Run first command

Complete here: ${data.setupUrl}

Need help? Check our Quick Start Guide: https://docs.agencyos.network/guides/quickstart

--
Mekong RaaS
  `.trim()

  return { subject, html, text }
}
