/**
 * Feedback & Setup Reminder Email Templates
 */

import type { EmailTemplate, FeedbackEmailData, SetupReminderEmailData } from './templates-types'

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
        ${[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => `<a href="${data.npsSurveyUrl}?score=${i}" class="nps-item">${i}</a>`).join('')}
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

export function createSetupReminderEmail(data: SetupReminderEmailData): EmailTemplate {
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
    <p><small>Need help? Check our <a href="https://www.mekongmind.com/docs/guides/quickstart">Quick Start Guide</a></small></p>
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

Need help? Check our Quick Start Guide: https://www.mekongmind.com/docs/guides/quickstart

--
Mekong RaaS
  `.trim()

  return { subject, html, text }
}
