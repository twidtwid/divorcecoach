#!/usr/bin/env python3
"""
Fastmail JMAP email client for DivorceCoach.

Read-only client for fetching and filtering emails related to divorce proceedings.
Designed to be invoked by Claude during sessions.
"""

import json
import sys
import requests
from pathlib import Path
from datetime import date
from typing import Optional, List, Dict, Any


# ============ Environment Loading ============

REPO_ROOT = Path(__file__).parent.parent


def load_env() -> dict:
    """Load environment variables from repo .env and home .env."""
    env_vars = {}

    # Load from repo .env
    env_path = REPO_ROOT / '.env'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()

    # Also check home .env for API keys (don't override repo values)
    home_env = Path.home() / '.env'
    if home_env.exists():
        for line in home_env.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                if key.strip() not in env_vars:
                    env_vars[key.strip()] = val.strip()

    return env_vars


# Load environment at module import
ENV = load_env()
FASTMAIL_TOKEN = ENV.get('FASTMAIL_JMAP_TOKEN')


# ============ Divorce Domain Filtering ============

DIVORCE_DOMAINS = {
    'lpeplaw.com',            # Todd's lawyers (LPEP)
    'thompsonaccounting.net',  # Forensic CPA (Megan Thompson)
    'strasenqdro.com',         # QDRO specialist (Jennifer)
    'flickerkerin.com',        # Opposing counsel
}


def _extract_domain(email_address: str) -> str:
    """Extract domain from an email address."""
    if '@' in email_address:
        return email_address.split('@')[1].lower()
    return ''


def _email_matches_divorce(email: dict) -> bool:
    """Check if an email involves a divorce domain (sender or any recipient)."""
    # Check sender
    if _extract_domain(email.get('sender_email', '')) in DIVORCE_DOMAINS:
        return True

    # Check recipients
    for recip in email.get('recipients', []):
        if _extract_domain(recip.get('email', '')) in DIVORCE_DOMAINS:
            return True

    return False


def filter_divorce_emails(emails: List[dict]) -> List[dict]:
    """Filter a list of emails to only those from/to divorce domains."""
    return [e for e in emails if _email_matches_divorce(e)]


# ============ Fastmail Client ============

class FastmailClient:
    """JMAP client for Fastmail API (read-only)."""

    def __init__(self, token: str = None):
        self.token = token or FASTMAIL_TOKEN
        if not self.token:
            raise ValueError("No Fastmail token provided. Set FASTMAIL_JMAP_TOKEN in .env")
        self.session_url = "https://api.fastmail.com/jmap/session"
        self.api_url = None
        self.account_id = None
        self.mailboxes = {}
        self._init_session()

    def _init_session(self):
        """Initialize JMAP session."""
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(self.session_url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        self.api_url = data['apiUrl']
        self.account_id = list(data['accounts'].keys())[0]

    def _call(self, methods: list) -> list:
        """Make JMAP API call."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
            "methodCalls": methods
        }
        resp = requests.post(self.api_url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()['methodResponses']

    def get_mailboxes(self) -> dict:
        """Get mailbox IDs (inbox, sent, archive)."""
        results = self._call([["Mailbox/get", {"accountId": self.account_id}, "0"]])
        for mb in results[0][1]['list']:
            role = mb.get('role')
            if role == 'inbox':
                self.mailboxes['inbox'] = mb['id']
            elif role == 'sent':
                self.mailboxes['sent'] = mb['id']
            elif role == 'archive':
                self.mailboxes['archive'] = mb['id']
        return self.mailboxes

    def get_emails_from_mailbox(self, mailbox_name: str, limit: int = 200,
                                 since_date: str = None) -> list:
        """Get emails from a specific mailbox.

        Args:
            mailbox_name: Key in self.mailboxes (e.g. 'inbox', 'sent')
            limit: Max emails to return
            since_date: ISO date string (YYYY-MM-DD) to filter after
        """
        if not self.mailboxes:
            self.get_mailboxes()

        mailbox_id = self.mailboxes.get(mailbox_name)
        if not mailbox_id:
            return []

        filter_obj = {"inMailbox": mailbox_id}
        if since_date:
            filter_obj["after"] = f"{since_date}T00:00:00Z"

        results = self._call([
            ["Email/query", {
                "accountId": self.account_id,
                "filter": filter_obj,
                "sort": [{"property": "receivedAt", "isAscending": False}],
                "limit": limit
            }, "0"],
            ["Email/get", {
                "accountId": self.account_id,
                "#ids": {"resultOf": "0", "name": "Email/query", "path": "/ids"},
                "properties": ["id", "from", "to", "subject", "preview", "receivedAt", "sentAt"]
            }, "1"]
        ])

        emails = []
        for e in results[1][1]['list']:
            sender = e['from'][0]['email'] if e.get('from') else ''
            sender_name = e['from'][0].get('name', '') if e.get('from') else ''

            recipients = []
            if e.get('to'):
                for to in e['to']:
                    recipients.append({
                        'email': to.get('email', ''),
                        'name': to.get('name', '')
                    })

            emails.append({
                'id': e['id'],
                'sender': f"{sender_name} <{sender}>",
                'sender_email': sender,
                'sender_name': sender_name,
                'recipients': recipients,
                'subject': e.get('subject', ''),
                'preview': e.get('preview', ''),
                'received': e.get('receivedAt', ''),
                'sent': e.get('sentAt', '')
            })
        return emails

    def get_inbox_emails(self, limit: int = 200, since_date: str = None) -> list:
        """Get emails from inbox."""
        return self.get_emails_from_mailbox('inbox', limit, since_date)

    def get_sent_emails(self, limit: int = 200, since_date: str = None) -> list:
        """Get emails from sent folder."""
        return self.get_emails_from_mailbox('sent', limit, since_date)

    def get_email_body(self, email_id: str) -> str:
        """Fetch the full text body of a specific email.

        Args:
            email_id: The JMAP email ID

        Returns:
            The plain text body of the email, or empty string if unavailable.
        """
        results = self._call([
            ["Email/get", {
                "accountId": self.account_id,
                "ids": [email_id],
                "properties": ["bodyValues", "textBody"],
                "fetchAllBodyValues": True
            }, "0"]
        ])

        email_data = results[0][1]['list']
        if not email_data:
            return ''

        email = email_data[0]
        body_values = email.get('bodyValues', {})
        text_body = email.get('textBody', [])

        # Get text from the first text body part
        for part in text_body:
            part_id = part.get('partId')
            if part_id and part_id in body_values:
                return body_values[part_id].get('value', '')

        # Fallback: return first available body value
        for part_id, bv in body_values.items():
            return bv.get('value', '')

        return ''

    def get_divorce_emails(self, since_date: str = None) -> Dict[str, List[dict]]:
        """Main entry point: get divorce-related emails from inbox and sent.

        Args:
            since_date: ISO date string (YYYY-MM-DD). Defaults to None (no date filter).

        Returns:
            {'inbox': [...], 'sent': [...]} with only divorce-domain emails.
        """
        inbox = self.get_inbox_emails(since_date=since_date)
        sent = self.get_sent_emails(since_date=since_date)

        return {
            'inbox': filter_divorce_emails(inbox),
            'sent': filter_divorce_emails(sent),
        }


# ============ CLI Entry Point ============

def _format_email_summary(email: dict, direction: str = 'received') -> str:
    """Format a single email for display."""
    dt = email.get('received', '') or email.get('sent', '')
    if dt:
        dt = dt[:16].replace('T', ' ')  # Trim to YYYY-MM-DD HH:MM

    if direction == 'sent':
        recips = ', '.join(r['email'] for r in email.get('recipients', []))
        who = f"To: {recips}"
    else:
        who = f"From: {email['sender_email']}"

    subject = email.get('subject', '(no subject)')
    preview = email.get('preview', '')[:100]

    return f"  [{dt}] {who}\n    Subject: {subject}\n    Preview: {preview}"


def main():
    since_date = None
    if len(sys.argv) > 1:
        since_date = sys.argv[1]  # Expected: YYYY-MM-DD

    client = FastmailClient()
    result = client.get_divorce_emails(since_date=since_date)

    date_label = f" since {since_date}" if since_date else ""

    print(f"\n=== Divorce-Related Inbox Emails{date_label} ({len(result['inbox'])}) ===")
    if result['inbox']:
        for email in result['inbox']:
            print(_format_email_summary(email, 'received'))
    else:
        print("  (none)")

    print(f"\n=== Divorce-Related Sent Emails{date_label} ({len(result['sent'])}) ===")
    if result['sent']:
        for email in result['sent']:
            print(_format_email_summary(email, 'sent'))
    else:
        print("  (none)")

    print()


if __name__ == '__main__':
    main()
