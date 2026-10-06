# CommunityBot

**AI-supported Discord community assistant for private onboarding, personalized recommendations, notifications, and project evaluation.**

CommunityBot was developed as part of the **Cooperation Systems** course at the University of Duisburg-Essen. The project explores how a Discord bot can help new members understand a community, discover relevant channels and events, and stay engaged over time.

## Highlights

- Private onboarding flow for new members
- Personalized channel and event recommendations
- Mistral LLM integration for AI-supported assistance
- Direct-message notifications for private recommendations
- User profiles stored in SQLite
- Administrative logging and evaluation tools
- Local Flask dashboard for reviewing project data
- Export workflow for evaluation data
- Environment-based secret management for API keys and bot tokens

## Tech Stack

- **Python**
- **Discord.py**
- **Mistral API**
- **Flask**
- **SQLite**
- **REST/API integration**
- **python-dotenv**

## Project Structure

```text
communitybot/
├── bot.py                # Main Discord bot and interaction flow
├── llm.py                # Mistral LLM integration and fallback logic
├── database.py           # SQLite persistence and data access
├── awareness.py          # Community-awareness functionality
├── discovery.py          # Discovery and recommendation support
├── dashboard.py          # Local Flask dashboard
├── export_evaluation.py  # Evaluation-data export
├── config.py             # Environment-based configuration
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment configuration
└── .gitignore
```

## Core Functionality

### Private Onboarding

New users begin in `#welcome` and can start a guided onboarding process. A private onboarding channel is created for the user so that profile information and recommendations are not exposed publicly.

After onboarding is completed, the temporary private channel is automatically removed.

### AI-Supported User Profiles

CommunityBot can use the **Mistral API** to transform onboarding answers into a structured user profile.

The implementation also includes fallback logic so the core onboarding flow can continue when the LLM service is unavailable.

### Personalized Recommendations

Based on onboarding information, the bot can support recommendations for relevant:

- community channels
- events
- discussion areas
- teammates or participation opportunities

Private recommendations are delivered through Discord direct messages.

### Administration and Evaluation

The project includes tools for examining community activity and evaluating the prototype, including:

- administrative logs
- evaluation summaries
- community-status information
- recent-log reports
- a local Flask dashboard
- exported evaluation data

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/sebghat77/communitybot.git
cd communitybot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Then add your own credentials to `.env`:

```env
DISCORD_TOKEN=your_discord_bot_token
MISTRAL_API_KEY=your_mistral_api_key
BOT_NAME=CommunityBot
```

> Never commit real API keys or Discord tokens. The `.env` file is excluded through `.gitignore`.

### 5. Start the bot

```bash
python bot.py
```

## Discord Server Setup

For a dedicated test server, an administrator can use:

```text
!setup_server
```

Useful commands include:

```text
!join
!project_help
!evaluation_summary
!community_status
!recent_logs 10
```

Administrative commands should only be used by authorized users in a test or project server.

## Local Dashboard

Start the dashboard with:

```bash
python dashboard.py
```

Then open:

```text
http://127.0.0.1:5000
```

The dashboard is intended for local project review and evaluation.

## Export Evaluation Data

Run:

```bash
python export_evaluation.py
```

This generates evaluation data that can be used for project analysis and reporting.

## Privacy and Security

The project is designed with basic privacy and security safeguards in mind:

- onboarding takes place in private user-specific channels
- recommendations can be delivered through direct messages
- secrets are loaded from environment variables
- `.env`, the local database, Python cache files, and exports are excluded from Git
- testers should use dedicated accounts and a dedicated Discord test server
- personal evaluation data should be removed or anonymized before public sharing

## My Contribution

I developed and integrated CommunityBot as part of the Cooperation Systems project. My work included:

- chatbot concept and interaction flow
- private onboarding
- Discord server setup
- recommendation and notification logic
- Mistral LLM integration
- administrative logging
- evaluation support
- dashboard and data export
- integration, debugging, and end-to-end testing

## Current Status

This repository represents an academic prototype and portfolio project. The application can be run locally with personal Discord and Mistral credentials.

Automated tests and CI are planned as the next engineering improvements.

## License

This project was created for academic and portfolio purposes. No open-source license has been added yet, so reuse is not automatically granted.
