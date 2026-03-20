#!/usr/bin/env python3
"""
Alertmanager Webhook Receiver
Forwards alerts to Twilio (SMS), Telegram, and Email

Usage:
    python alert-webhook-server.py

Environment variables:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - TWILIO_FROM_NUMBER
    - TWILIO_TO_NUMBER
    - TELEGRAM_BOT_TOKEN
    - TELEGRAM_CHAT_ID
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import urllib.request
import urllib.error

# Twilio imports
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("Twilio library not installed. SMS notifications disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '')
TWILIO_TO_NUMBER = os.environ.get('TWILIO_TO_NUMBER', '')

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# ─────────────────────────────────────────────────────────────────────────────
# Notification Handlers
# ─────────────────────────────────────────────────────────────────────────────


def send_sms_twilio(message: str) -> bool:
    """Send SMS via Twilio"""
    if not TWILIO_AVAILABLE:
        logger.error("Twilio library not available")
        return False

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER]):
        logger.error("Twilio credentials not configured")
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=TWILIO_TO_NUMBER
        )
        logger.info(f"SMS sent: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False


def send_telegram(message: str) -> bool:
    """Send message via Telegram bot"""
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        logger.error("Telegram credentials not configured")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = json.dumps({
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }).encode('utf-8')

    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            logger.info(f"Telegram message sent: {response.status}")
            return True
    except urllib.error.URLError as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def format_alert_message(alerts: list) -> str:
    """Format alerts into readable message"""
    messages = []
    for alert in alerts:
        status = alert.get('status', 'unknown')
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})

        emoji = "🚨" if status == 'firing' else "✅"
        severity = labels.get('severity', 'unknown')
        alertname = labels.get('alertname', 'Unknown')
        instance = labels.get('instance', 'unknown')

        summary = annotations.get('summary', 'No summary')
        description = annotations.get('description', 'No description')

        msg = (
            f"{emoji} *{alertname}* ({severity})\n"
            f"Status: {status}\n"
            f"Instance: {instance}\n"
            f"Summary: {summary}\n"
            f"Description: {description}"
        )
        messages.append(msg)

    return "\n\n".join(messages)


# ─────────────────────────────────────────────────────────────────────────────
# HTTP Handler
# ─────────────────────────────────────────────────────────────────────────────


class WebhookHandler(BaseHTTPRequestHandler):
    """Handle Alertmanager webhook callbacks"""

    def do_POST(self):
        """Handle POST webhook from Alertmanager"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            self.send_response(400)
            self.end_headers()
            return

        # Parse alerts
        alerts = payload.get('alerts', [])
        if not alerts:
            logger.warning("No alerts in payload")
            self.send_response(200)
            self.end_headers()
            return

        # Format message
        message = format_alert_message(alerts)
        logger.info(f"Processing {len(alerts)} alert(s)")

        # Route based on alert type
        sent_sms = False
        sent_telegram = False

        for alert in alerts:
            alertname = alert.get('labels', {}).get('alertname', '')
            severity = alert.get('labels', {}).get('severity', '')

            # Critical or CircuitBreaker → SMS + Telegram
            if severity == 'critical' or alertname == 'CircuitBreakerOpen':
                if not sent_sms:
                    send_sms_twilio(message)
                    sent_sms = True
                if not sent_telegram:
                    send_telegram(message)
                    sent_telegram = True
            # Warning → Telegram only
            elif severity == 'warning':
                if not sent_telegram:
                    send_telegram(message)
                    sent_telegram = True

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def do_GET(self):
        """Health check endpoint"""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Alert Webhook Running')

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info("%s - %s", self.address_string(), format % args)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    port = int(os.environ.get('WEBHOOK_PORT', 5001))
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    logger.info(f"Alert Webhook Server starting on port {port}")
    logger.info(f"Twilio configured: {bool(TWILIO_AVAILABLE and TWILIO_ACCOUNT_SID)}")
    logger.info(f"Telegram configured: {bool(TELEGRAM_BOT_TOKEN)}")
    server.serve_forever()


if __name__ == '__main__':
    main()
