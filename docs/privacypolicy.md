---
layout: default
title: Privacy Policy
nav_order: 10
---

<h1 style="text-align: center">Privacy Policy</h1>

_Last Updated: 30/08/2026_

# Introduction

This privacy policy outlines how Forum Manager ("we," "our," or "us") collects, uses, and protects your (the end user) personal data when you interact with the Forum Manager bot. By using Forum Manager, you agree to the terms and conditions of this policy.

References in this document may refer to servers as guilds, as that is the terminology used within Discord's API.

## Short Version

Forum Manager moderates Discord forum channels according to rules that server administrators configure. It reads the text of posts in forum channels an administrator has explicitly registered with the bot, checks them against that server's own rules, and acts on the result. **We do not store the content of your messages.** The only personal data held in our database is the Discord ID of a server's owner, kept for as long as the bot is in that server. We do not sell, lease, or distribute data to third parties, and we never use your data to train machine learning or AI models.

## What Data Do We Collect?

### Servers

- Guild ID
- Guild name and member count
- The guild owner's Discord ID and username
- Premium expiry date, where applicable
- Visibility and activity status
- Created, updated, and deletion timestamps

### Configuration

Settings written by server staff: configured channel IDs, role IDs, and feature toggles, stored against the guild they belong to.

### Forums

Per-forum settings written by server staff: the forum channel ID, its name, minimum character requirements, reminder text, duplicate-detection settings, moderation patterns (blacklisted words and regular expressions), and cleanup rules.

### Staff

Discord IDs of Forum Manager's own staff members, used to gate privileged bot commands. This does not include staff of servers using the bot.

## Message Content

Forum Manager uses Discord's Message Content intent. This section explains exactly what that means in practice.

**Where content is read.** Only in forum channels that a server administrator has explicitly registered with the bot using `/forum add` or `/forum add_all`. Forum Manager does not read messages in channels that have not been registered.

**What is done with it.** The text of a post is checked in memory against the rules that server has configured — a minimum character count, a blacklisted-word list, and administrator-authored regular expressions that block a post, flag it to a moderator log, or require it to contain particular information. The text is also compared against that author's other posts in the same forum to detect duplicates. Once these checks complete, the content is discarded.

**What is retained.** Nothing in our database. When a post is actioned, an explanation is posted to the moderation log channel *within that server's own Discord* and, where configured, sent to the post's author by direct message. Those records live in Discord, under the control of the server that configured them.

**Exports.** Server staff with the Manage Threads permission can use `/export` to produce an HTML archive of a thread, forum, or channel for record-keeping. These archives contain the full text and attachments of the messages in scope and are delivered to the requesting staff member by direct message. Archives larger than 24 MB are uploaded to our download service and returned as a one-time, password-protected link; those files are held only for as long as needed to deliver them. Archives are generated only when a member of that server's staff explicitly requests one.

**Can users opt out?** Forum Manager does not currently offer a per-user opt-out of message content processing. Content is processed only in forum channels a server administrator has registered, and is not retained by us. If you do not wish your posts to be processed, do not post in the forum channels a server has placed under Forum Manager's moderation; server staff can tell you which those are.

## AI and Machine Learning

Message content, and any other data collected by Forum Manager, is **never** used to train machine learning or AI models, and is never supplied to third-party model providers.

## Legal Basis for Data Collection

We process this data under the lawful basis of **legitimate interest** — the interest of Discord communities in moderating their own forum channels effectively, under rules those communities define themselves.

## Data Minimization

We collect only the minimum data required to operate the features a server has enabled. We do not build profiles of users, we do not track users between servers, and we do not retain message content.

## Retention Policy and Data Lifecycles

- **Server records:** retained while Forum Manager is a member of the guild. When the bot is removed, the record is marked deleted and then **permanently erased after 30 days**, together with all configuration, forum settings, patterns, and cleanup rules belonging to it. The 30-day window exists so that a server which re-invites the bot does not lose its configuration. This is enforced automatically by a scheduled routine, not manually.
- **Operational logs:** log files may contain Discord IDs recorded during normal operation. They are rotated and **permanently deleted after 7 days**.
- **Message content:** not retained. Processed in memory and discarded.
- **Export archives:** delivered to the requesting staff member and not retained by us, beyond the temporary storage needed to deliver oversized archives via a one-time link.

## How We Store and Protect Your Data

Data is transmitted between Discord and Forum Manager over TLS and stored in a database local to the bot. The storage holding that database is **encrypted at rest** using full-disk encryption, and access is restricted to the bot's operators. Our download service, used for oversized export archives, is subject to the same protections.

## Data Sharing

We do not share user data with third parties unless required by law or to comply with legal obligations. We will never sell, lease, or otherwise distribute user data to unauthorized third parties.

## User Rights

In accordance with the **General Data Protection Regulation (GDPR)**, users have the following rights regarding personal data:

### Access to User Data

- Users have the right to request a copy of the personal data we hold about them.

### Correction of Inaccurate Data

- If a user believes any data we hold is incorrect or incomplete, they can request corrections.

### Data Deletion

- Users have the right to request the deletion of their personal data where applicable.

Because Forum Manager does not retain message content and stores no per-member records, in most cases we hold no personal data about an individual user at all. The exception is server owners, whose Discord ID is stored for the servers they own.

## Processing of Requests

All requests will be responded to within **30 days** of submission, in accordance with our retention policy and applicable legal obligations.

### How to Make These Requests?

To make a request, you can:

- Run `/privacy` in any server running Forum Manager, which shows these contact routes and a link to this policy.
- Join our support guild and open a ticket.
- Send an email to **rico@strykerdevelopment.com**.

Server administrators can remove all data held for their server immediately by removing Forum Manager from that server; the record is then permanently erased within 30 days as described above.

**Note:** Excessive or unreasonable requests may incur a fee or be ignored, in accordance with GDPR regulations.

## Q&A

**Q: Can the bot read my messages?**
A: In forum channels a server administrator has registered with the bot, yes — that is how the moderation rules are enforced. It does not read messages in channels that have not been registered, and it does not keep what it reads.

**Q: Does the bot store what I post?**
A: No. Post text is checked against the server's rules in memory and discarded. If a post breaks a rule, an explanation is logged into that server's own Discord channel.

**Q: Can the bot read my DMs?**
A: If you DM the bot, it can read those messages. It has no access to your private DMs with other users.

**Q: Is my data used to train AI?**
A: No. Never.

**Q: Can the bot see my IP address, email, or payment details?**
A: No. Discord does not expose any of that to bots.

**Q: What happens to my server's data if I remove the bot?**
A: It is marked deleted immediately and permanently erased 30 days later, along with every setting belonging to it. Re-inviting the bot within that window restores your configuration.

## Data Breach Policy

In the event of a data breach, we will:

- Notify affected users within **72 hours**.
- Take immediate steps to secure data and prevent further breaches.
- Notify the relevant authorities.

## Updates to This Policy

We may update this policy from time to time. Any changes will be communicated through our support guild or other appropriate channels. Continued use of Forum Manager after updates constitutes acceptance of the revised policy.
