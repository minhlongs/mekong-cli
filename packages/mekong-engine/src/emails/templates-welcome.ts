/**
 * Welcome & Verification Email Templates
 */

import type { EmailTemplate, WelcomeEmailData, VerificationEmailData } from './templates-types'

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
      <li><a href="https://www.mekongmind.com/docs/guides/commands">Command Reference</a></li>
      <li><a href="https://discord.gg/mekong">Join our Discord community</a></li>
    </ul>
    <p>Need help? Reply to this email or join our Discord. We're here to help you succeed! 🙌</p>
  </div>
  <div class="footer">
    <p>Mekong RaaS - AI-operated business platform</p>
    <p>Questions? Contact us at hello@mekongmind.com</p>
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
- Command Reference: https://www.mekongmind.com/docs/guides/commands
- Discord: https://discord.gg/mekong

Need help? Reply to this email or join our Discord!

--
Mekong RaaS - AI-operated business platform
  `.trim()

  return { subject, html, text }
}

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
