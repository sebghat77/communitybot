# CommunityBot

**An AI-supported Discord chatbot for onboarding, community participation, personalized recommendations, and project evaluation.**

CommunityBot was developed as part of the **Cooperation Systems** course. It helps new members understand a Discord community, complete a private onboarding process, discover relevant channels and events, and receive useful notifications without exposing personal recommendations to other users.

---

## Project Overview

Online communities can be difficult for new members to understand. Users may not know:

- where to introduce themselves;
- which channels are relevant;
- how to find people with similar interests;
- which events or activities are available;
- how to remain active after joining.

CommunityBot addresses these problems through structured onboarding, private guidance, AI-supported recommendations, notifications, and administrative evaluation tools.

---

## Main Features

### Private Onboarding

- New users start from the public `#welcome` channel.
- After selecting **Start Onboarding**, each user receives a private onboarding channel.
- Only the user, the bot, and administrators can access that channel.
- Users who write elsewhere before completing onboarding are redirected to their private onboarding channel.
- After onboarding is completed, the private channel is automatically deleted after approximately 90 seconds.

### Personalized Recommendations

- The bot can recommend relevant channel ideas and event ideas.
- Virtual recommendations are sent privately through Discord direct messages.
- Recommendations are not posted publicly, preventing other users from interacting with another person's notification.

### Community Notifications

- Real event and channel notifications are sent through direct messages.
- Discord pop-up behavior depends on the notification settings of each user.

### AI-Supported Assistance

- The bot uses the Mistral API for AI-supported functionality.
- API credentials are stored as environment variables and must never be committed to the repository.

### Administration and Evaluation

Administrators can review activity and evaluation information through:

- `#bot-logs`
- evaluation summary commands;
- community status reports;
- recent log reports;
- a local dashboard;
- exported evaluation data.

---

## About the Developer

**Sebghatullah Yarzada** developed and integrated CommunityBot as part of the Cooperation Systems project.

The work focused on:

- chatbot concept and interaction flow;
- private onboarding;
- Discord server setup;
- recommendations and notifications;
- administrative logging;
- evaluation support;
- dashboard and data export;
- integration and testing of the complete system.

---

## Technology

- **Language:** Python
- **Platform:** Discord
- **AI service:** Mistral API
- **Dashboard:** Local web dashboard
- **Configuration:** Environment variables through a `.env` file

---

## Requirements

Before running the project, prepare:

- Python 3;
- a Discord account;
- a Discord test server;
- a Discord bot token;
- a Mistral API key;
- the required Python packages from `requirements.txt`.

> Use a separate Discord server for testing. Some administrative setup commands can create or delete channels.

---

## Installation

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd YOUR_REPOSITORY_FOLDER
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the Environment File

On Windows PowerShell:

```powershell
copy .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

### 4. Add Environment Variables

Open `.env` and add fresh credentials:

```env
DISCORD_TOKEN=your_discord_bot_token
MISTRAL_API_KEY=your_mistral_api_key
BOT_NAME=CommunityBot
```

> **Security:** Never publish the `.env` file or real API tokens. Make sure `.env` is included in `.gitignore`. If a token was previously committed, revoke it and create a new one before making the repository public.

### 5. Start the Bot

```bash
python bot.py
```

The bot is online only while this process is running.

---

## Initial Discord Server Setup

In a new test server, an administrator can run:

```text
!setup_server
```

Useful starting commands include:

```text
!join
!project_help
```

The current user experience is designed around the **Start Onboarding** entry point in `#welcome`. The commands above are also useful during setup and testing when enabled by the bot configuration.

---

## How Recruiters, Instructors, or Testers Can Try the Bot

### Option A: Public Test Server

Add a limited public Discord invite to this section:

**Discord Test Server:** `ADD_PUBLIC_TEST_SERVER_INVITE`

Recommended test flow:

1. Join the Discord test server.
2. Open `#welcome`.
3. Select **Start Onboarding**.
4. Continue inside the private onboarding channel created for you.
5. Complete the onboarding questions.
6. Check your Discord direct messages for recommendations or notifications.
7. Use `!project_help` to view available help or project-related commands.
8. Observe how the private onboarding channel is removed after onboarding is completed.

Regular testers should not receive administrator permissions.

### Option B: Run Locally

Technical reviewers can clone the repository, add their own Discord and Mistral credentials, invite their bot application to a private Discord test server, and follow the installation steps above.

### Suggested Test Cases

| Test | Expected Result |
|---|---|
| A new user opens `#welcome` | The user can start onboarding |
| A user starts onboarding | A private onboarding channel is created |
| An unfinished user writes elsewhere | The bot redirects the user to onboarding |
| A user completes onboarding | The flow finishes and the private channel is later deleted |
| A recommendation is generated | The user receives it privately |
| Another member checks public channels | They cannot interact with another user's private notification |
| An administrator checks logs | Activity is visible in `#bot-logs` |
| The bot process stops | The bot appears offline |

---

## Evaluation Commands

Administrators can use:

```text
!evaluation_summary
!community_status
!recent_logs 10
```

Administrative reports are sent to:

```text
#bot-logs
```

These commands are intended for project evaluation and should normally be restricted to administrators.

---

## Dashboard

Start the local dashboard with:

```bash
python dashboard.py
```

Then open:

```text
http://127.0.0.1:5000
```

The dashboard is intended for local review and evaluation. It is not automatically a public web application.

---

## Export Evaluation Data

Run:

```bash
python export_evaluation.py
```

This creates an export that can be used for project analysis and reporting.

---

## Clean Test Server Setup

If the test server contains old project channels or test data, an administrator can run:

```text
!fresh_setup CONFIRM
```

> **Warning:** This command deletes old channels or categories and rebuilds the project structure. Use it only in a dedicated test or project server.

---

## 24/7 Hosting

The bot works only while:

```bash
python bot.py
```

is running.

For continuous access, deploy it to a service that supports long-running Python applications, such as Railway, Render, Fly.io, Replit, or a VPS.

Configure these environment variables on the hosting platform:

```text
DISCORD_TOKEN
MISTRAL_API_KEY
BOT_NAME
```

Use this start command:

```text
python bot.py
```

Do not place real credentials inside the repository or deployment configuration files committed to GitHub.

---

## Privacy and Responsible Testing

- Use test accounts and a dedicated test server.
- Do not collect unnecessary personal information.
- Inform testers when activity is logged for evaluation.
- Keep API keys and Discord tokens private.
- Do not give public testers administrator permissions.
- Remove or anonymize personal evaluation data before sharing it publicly.

---

## Repository Links

Replace the placeholders below before adding the project to a résumé:

- **GitHub Repository:** `ADD_GITHUB_REPOSITORY_URL`
- **Discord Test Server:** `ADD_PUBLIC_TEST_SERVER_INVITE`
- **Demo Video:** `ADD_DEMO_VIDEO_URL` *(optional)*

---

## Résumé Description

**CommunityBot — AI-Supported Discord Community Assistant**

Developed an AI-supported Discord chatbot that provides private onboarding, personalized channel and event recommendations, direct-message notifications, administrative logging, and evaluation tools. Implemented the complete interaction flow, server setup, dashboard, and data-export workflow using Python, Discord, and the Mistral API.

---

## Current Version Behavior

- `#welcome` contains the public Start Onboarding entry point.
- Each user receives a private onboarding channel.
- The private channel is visible only to the user, the bot, and administrators.
- The channel is deleted automatically after completed onboarding.
- Virtual recommendations are sent only by direct message.
- Real event and channel notifications are sent only by direct message.
- Administrative visibility is maintained through `#bot-logs`.

---

## License

This repository was created for an academic project and portfolio presentation. Before allowing external reuse or contributions, add an appropriate `LICENSE` file and clarify the permitted terms of use.
