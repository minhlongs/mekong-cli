/** Handlebars email template engine with 6 built-in templates */
import Handlebars from 'handlebars';

export interface RenderedEmail {
  subject: string;
  body: string;
}

const BUILT_IN_TEMPLATES: Record<string, string> = {
  invoice_send: `Subject: Invoice {{invoiceNumber}} from {{companyName}}
Hi {{customerName}},

Please find attached invoice {{invoiceNumber}} for {{amount}} {{currency}}, due on {{dueDate}}.

{{#if items}}
Items:
{{#each items}}- {{description}}: {{quantity}} x {{unitPrice}} = {{total}}
{{/each}}{{/if}}
Total: {{amount}} {{currency}}

Pay online: {{paymentUrl}}

Thank you,
{{companyName}}`,

  payment_received: `Subject: Payment Received — Thank You, {{customerName}}!
Hi {{customerName}},

We have received your payment of {{amount}} {{currency}} on {{date}}.

Reference: {{invoiceNumber}}

Your account is up to date.

Thank you for your business,
{{companyName}}`,

  payment_overdue: `Subject: Overdue Invoice {{invoiceNumber}} — Action Required
Hi {{customerName}},

Invoice {{invoiceNumber}} for {{amount}} {{currency}} was due on {{dueDate}} and remains unpaid.

Please make payment as soon as possible to avoid service interruption.

Pay online: {{paymentUrl}}

If you have already paid, please disregard this message.

{{companyName}}`,

  welcome: `Subject: Welcome to {{companyName}}, {{customerName}}!
Hi {{customerName}},

Welcome aboard! We are thrilled to have you with us.

{{#if nextSteps}}
Here is how to get started:
{{#each nextSteps}}- {{this}}
{{/each}}{{/if}}
If you have any questions, reply to this email.

{{companyName}}`,

  follow_up: `Subject: Following up — {{subject}}
Hi {{contactName}},

I wanted to follow up on {{subject}}.

{{message}}

Would you be available for a quick call this week?

Best regards,
{{senderName}}
{{companyName}}`,

  support_reply: `Subject: Re: [{{ticketId}}] {{originalSubject}}
Hi {{customerName}},

Thank you for reaching out to {{companyName}} support.

{{response}}

{{#if resolved}}Your ticket has been marked as resolved.{{else}}We will continue working on this.{{/if}}

Ticket ID: {{ticketId}}

Best regards,
{{agentName}}
{{companyName}} Support`,
};

export class EmailTemplateEngine {
  private templates = new Map<string, HandlebarsTemplateDelegate>();

  constructor() {
    for (const [name, source] of Object.entries(BUILT_IN_TEMPLATES)) {
      this.templates.set(name, Handlebars.compile(source));
    }
  }

  render(templateName: string, data: Record<string, unknown>): RenderedEmail {
    const compiled = this.templates.get(templateName);
    if (!compiled) throw new Error(`Template '${templateName}' not found`);

    const output = compiled(data);
    const lines = output.split('\n');
    const subjectLine = lines[0] ?? '';
    const subject = subjectLine.startsWith('Subject: ')
      ? subjectLine.slice('Subject: '.length).trim()
      : subjectLine.trim();
    const body = lines.slice(1).join('\n').replace(/^\n/, '');
    return { subject, body };
  }

  registerTemplate(name: string, source: string): void {
    this.templates.set(name, Handlebars.compile(source));
  }

  listTemplates(): string[] {
    return Array.from(this.templates.keys());
  }
}
