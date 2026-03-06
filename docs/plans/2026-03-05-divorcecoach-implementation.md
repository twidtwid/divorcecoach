# DivorceCoach Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a lightweight command center that helps Todd close out his divorce through email triage, next-action coaching, and status tracking.

**Architecture:** CLAUDE.md-driven — no database, no custom commands. Email access via Fastmail JMAP. Reference docs in `docs/refs/`. Living status in `STATUS.md`.

**Tech Stack:** Python 3 (email client), Fastmail JMAP API, Claude Code CLAUDE.md

---

### Task 1: Set up repo structure

**Files:**
- Create: `scripts/` directory
- Create: `docs/refs/` directory
- Create: `.env` (with Fastmail token)
- Create: `.last_session`

**Step 1: Create directory structure**

```bash
mkdir -p scripts docs/refs
```

**Step 2: Create .env with Fastmail token**

Read the `FASTMAIL_JMAP_TOKEN` value from `/Users/todd_1/repo/claude/lifecoach/.env` and create a `.env` file in this repo with it. Also add it to `.gitignore`.

**Step 3: Create .last_session timestamp file**

```bash
echo "2025-01-01T00:00:00" > .last_session
```

Set it to an old date so the first session picks up everything recent.

**Step 4: Update .gitignore**

Add `.env` and `.last_session` to `.gitignore`.

**Step 5: Commit**

```bash
git add -A
git commit -m "chore: set up repo structure with scripts/, docs/refs/, .env, .last_session"
```

---

### Task 2: Create email client

**Files:**
- Create: `scripts/email_client.py`

Adapt from `/Users/todd_1/repo/claude/lifecoach/scripts/email_utils.py`. Keep only what's needed:

- `FastmailClient` class (JMAP session init, mailbox listing, email fetching from inbox and sent)
- `.env` loading
- Helper functions (`clean_sender`, `extract_email_address`, `format_email_line`)

Strip out: Pushover, Ollama/LLM classification, Gmail client, Anthropic client. This is a read-only tool for Claude to invoke during sessions.

**Step 1: Write `scripts/email_client.py`**

Core structure:
```python
#!/usr/bin/env python3
"""
Fastmail JMAP email client for DivorceCoach.
Fetches emails from divorce-related contacts.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent

# Divorce-related domains
DIVORCE_DOMAINS = {
    'lpeplaw.com',            # Todd's lawyers (LPEP)
    'thompsonaccounting.net',  # Forensic CPA (Megan Thompson)
    'strasenqdro.com',         # QDRO specialist (Jennifer)
    'flickerkerin.com',        # Opposing counsel
}

# Known contacts for display
DIVORCE_CONTACTS = {
    'lpeplaw.com': 'LPEP Law (your attorneys)',
    'thompsonaccounting.net': 'Thompson Accounting (forensic CPA)',
    'strasenqdro.com': 'Strasen Law (QDRO)',
    'flickerkerin.com': 'Flicker Kerin (opposing counsel)',
}

def load_env() -> dict: ...
def load_token() -> str: ...

class FastmailClient:
    def __init__(self, token): ...
    def _init_session(self): ...
    def _call(self, methods): ...
    def get_mailboxes(self): ...
    def get_emails_from_mailbox(self, mailbox, limit, since_date): ...
    def get_inbox_emails(self, limit=200, since_date=None): ...
    def get_sent_emails(self, limit=200, since_date=None): ...

def filter_divorce_emails(emails: list) -> list:
    """Filter to only divorce-domain emails."""
    ...

def get_divorce_emails(since_date: str = None) -> dict:
    """Main entry point. Returns {'inbox': [...], 'sent': [...]}."""
    ...

if __name__ == '__main__':
    # CLI usage: python scripts/email_client.py [since_date]
    import sys
    since = sys.argv[1] if len(sys.argv) > 1 else None
    results = get_divorce_emails(since)
    for folder, emails in results.items():
        print(f"\n=== {folder.upper()} ({len(emails)} divorce emails) ===")
        for e in emails:
            print(f"  {e['received'][:10]} | {e['sender_name'] or e['sender_email']} | {e['subject']}")
```

**Step 2: Test it works**

```bash
cd /Users/todd_1/repo/claude/divorcecoach
python3 scripts/email_client.py 2025-01-01
```

Should show divorce-related emails from inbox and sent.

**Step 3: Commit**

```bash
git add scripts/email_client.py
git commit -m "feat: add Fastmail JMAP email client for divorce contacts"
```

---

### Task 3: Organize reference documents

**Files:**
- Move existing converted docs to `docs/refs/`
- Copy remaining converted docs from `/tmp/divorce_docs/`

**Step 1: Move already-converted docs**

The repo root has some .md files from earlier conversion. Move them to `docs/refs/`:

```bash
mv "2024-12-17_121724 Stipulation re settlement Final Settlement v2_CM, CD - signed.md" docs/refs/settlement-stipulation.md
mv "2024-12-17_2024.12.17  Dailey-Asset Allocation Spreadsheet (Divide Equally).md" docs/refs/asset-allocation.md
mv DIVORCE_TIMELINE.md docs/refs/divorce-timeline.md
```

**Step 2: Copy remaining useful docs from /tmp**

```bash
cp "/tmp/divorce_docs/2025-12-05_Dailey (Marriage of) 90030 Invoice 12_5_2025.md" docs/refs/latest-invoice-2025-12.md
```

Note: The mediation brief (5MB), retainer letter (91K), and QDRO form (516K) are very large due to embedded images. These are better referenced from the source PDFs in `/Users/todd_1/repo/divorce/` on demand rather than committed to the repo.

**Step 3: Commit**

```bash
git add docs/refs/
git commit -m "docs: organize reference documents (settlement, assets, timeline, invoice)"
```

---

### Task 4: Create STATUS.md

**Files:**
- Create: `STATUS.md`

**Step 1: Write STATUS.md**

Based on document analysis, create the initial status tracker:

```markdown
# Divorce Status Tracker

**Case:** Todd Dailey v. Cheryl Dailey (19FL004454)
**Settlement signed:** December 17, 2024
**Goal:** Final judgment entered by court

## Open Workstreams

### 1. Pay Lawyers (LPEP Law)
- **Status:** NEEDS ATTENTION
- **Trust balance:** $1,334.00 (as of Dec 2025 invoice)
- **Replenishment requested:** $3,666.00
- **Contact:** Quinn Youngs / Lisa Mori at lpeplaw.com
- **Next action:** Pay trust replenishment

### 2. Pay Forensic CPA (Thompson Accounting)
- **Status:** UNKNOWN — need to check emails
- **Contact:** Megan Thompson / Ashley Nguyen at thompsonaccounting.net
- **Next action:** Determine outstanding balance

### 3. QDRO Execution (Strasen Law)
- **Status:** IN PROGRESS — QDRO request form dated Jan 2026
- **Contact:** Jennifer at strasenqdro.com
- **Next action:** Confirm QDRO status, what's needed from Todd

### 4. Asset Split / Deed Transfer
- **Status:** NEEDS ATTENTION
- **Todd owes Cheryl:** ~$726,713 per allocation spreadsheet
- **Key assets:** Real property (125 Dana Ave?), retirement accounts, Apple stock/RSUs
- **Next action:** Clarify with lawyer what transfers remain

### 5. Final Judgment Filing
- **Status:** BLOCKED (waiting on 1-4)
- **Next action:** Complete all above, lawyer files with court

## Payment Log

| Date | Payee | Amount | Method | Notes |
|------|-------|--------|--------|-------|
| (to be filled as payments are made) | | | | |

## Key Contacts

| Name | Role | Email Domain | Notes |
|------|------|-------------|-------|
| Mitchell Ehrlich | Lead counsel | lpeplaw.com | |
| Quinn Youngs | Associate | lpeplaw.com | Handles recent billing |
| Lisa Mori | Paralegal | lpeplaw.com | |
| Megan Thompson | Forensic CPA | thompsonaccounting.net | Court-appointed expert |
| Ashley Nguyen | CPA team | thompsonaccounting.net | |
| Jennifer | QDRO specialist | strasenqdro.com | |
| Flicker Kerin LLP | Opposing counsel | flickerkerin.com | Cheryl's side |

## Completion Checklist

- [ ] All lawyer fees paid / trust funded
- [ ] Forensic CPA paid
- [ ] QDRO executed (retirement accounts split)
- [ ] Real property deed transferred
- [ ] Asset equalization payment made to Cheryl
- [ ] All documents signed and filed
- [ ] Final judgment entered by court
- [ ] Case closed
```

**Step 2: Commit**

```bash
git add STATUS.md
git commit -m "feat: add STATUS.md with workstreams, contacts, completion checklist"
```

---

### Task 5: Write CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

This is the most important file — it's what makes every session useful.

**Step 1: Write CLAUDE.md**

Key sections:

1. **Session Startup Routine** — Auto-gather new info on session start
2. **Case Context** — Full background so Claude has zero-shot understanding
3. **Coaching Rules** — Anxiety-aware interaction patterns
4. **Email Access** — How to use the email client
5. **Reference Docs** — Where to find key documents
6. **Source Documents** — Path to full PDF archive

The session startup section should instruct Claude to:
```
On EVERY new session:
1. Read STATUS.md for current state
2. Read .last_session for last activity timestamp
3. Run: python3 scripts/email_client.py <last_session_date>
4. Check for new files: find /Users/todd_1/repo/divorce/ -newer .last_session -type f
5. Present brief status: what's new, what's urgent, ONE recommended next action
6. Update .last_session with current timestamp when session ends
```

The coaching rules section should include:
- Lead with ONE concrete next action
- Break big tasks into tiny first steps
- Never shame about delays — "let's just pick up where we are"
- Celebrate any completed action
- Anne is a supportive partner who can help — suggest involving her when appropriate
- Frame everything as "closing this chapter" not "the divorce"
- When Todd seems stuck, suggest the smallest possible step
- If multiple things are urgent, pick the one that unblocks others

The case context section should include:
- Parties, case number, court
- Settlement terms summary (signed Dec 2024, equal split, Todd owes ~$726K)
- Key asset categories (real property, retirement accounts, Apple RSUs, brokerage)
- All contacts with roles
- Source document archive path: `/Users/todd_1/repo/divorce/`

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "feat: add CLAUDE.md with case context, coaching rules, session startup"
```

---

### Task 6: Initial email triage and STATUS.md update

**Step 1: Run the email client to get recent divorce emails**

```bash
python3 scripts/email_client.py 2025-06-01
```

**Step 2: Review results and update STATUS.md**

Based on what the emails reveal:
- Update payment statuses
- Fill in any unknown amounts (especially forensic CPA)
- Update QDRO status
- Note any action items from lawyers

**Step 3: Commit**

```bash
git add STATUS.md
git commit -m "feat: update STATUS.md with current email triage"
```

---

### Task 7: Push to GitHub

**Step 1: Push all commits**

```bash
git push origin main
```

---
