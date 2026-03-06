# DivorceCoach Design

## Problem

Todd has a 6+ year divorce (case 19FL004454, Todd v. Cheryl Dailey) with a signed settlement (Dec 2024) that needs to be executed to completion. Due to avoidant anxiety, he's been ignoring emails and delaying action. He needs a system that cuts through the fog, tells him what to do next, and helps him do it.

## Solution

A lightweight Claude Code command center — no database, no slash commands. Just a well-organized repo with deep case context in CLAUDE.md, an email client for Fastmail JMAP access, reference documents, and a living STATUS.md tracker.

## Architecture

### Core Files

- **`CLAUDE.md`** — Case context, contacts, coaching rules, session startup instructions
- **`STATUS.md`** — Living tracker: workstreams, payments, next actions, completion checklist
- **`.last_session`** — Timestamp file for tracking what's new between sessions
- **`.env`** — Fastmail JMAP token (symlinked from lifecoach or copied)

### Scripts

- **`scripts/email_client.py`** — Fastmail JMAP client adapted from lifecoach's `email_utils.py`

### Reference Docs

- **`docs/refs/`** — Converted key documents (settlement, asset allocation, timeline, etc.)

## Session Startup Behavior

On every new session, Claude automatically:

1. Checks `.last_session` for when Todd was last active
2. Scans `/Users/todd_1/repo/divorce/` for new files since last session
3. Fetches inbox + sent emails from divorce domains since last session
4. Presents a brief status update with top priority action

## Workstreams to "Done"

1. **Pay lawyers** — LPEP trust replenishment + outstanding balance
2. **Pay forensic CPA** — Megan Thompson at Thompson Accounting
3. **QDRO execution** — Retirement account splitting via Strasen Law
4. **Asset split / deed transfer** — Todd owes Cheryl ~$726,713
5. **Court filing** — Final judgment entry = legally done

## Coaching Rules

- Lead with ONE next action, not a wall of tasks
- Break big things into tiny first steps
- Never shame about delays or avoidance
- Celebrate completion of any step
- Anne can be looped in as accountability partner
- Frame as "closing this chapter" not "dealing with the divorce"

## "Done" Criteria

Judgment entered by the court. Divorce legally final, all assets transferred, QDROs executed, deeds recorded.
