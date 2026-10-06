# CommunityBot

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img alt="Discord.py" src="https://img.shields.io/badge/Discord.py-5865F2?logo=discord&logoColor=white">
  <img alt="Mistral AI" src="https://img.shields.io/badge/Mistral%20AI-FF7000?logo=mistralai&logoColor=white">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white">
  <img alt="HTML5" src="https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white">
  <img alt="CSS3" src="https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white">
  <img alt="Pytest" src="https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=white">
  <img alt="GitHub Actions" src="https://img.shields.io/badge/GitHub%20Actions-2088FF?logo=githubactions&logoColor=white">
</p>

[![Tests](https://github.com/sebghat77/communitybot/actions/workflows/tests.yml/badge.svg)](https://github.com/sebghat77/communitybot/actions/workflows/tests.yml)

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

## Tech

Python · Discord.py · Mistral API · Flask · SQLite · HTML/CSS · REST API integration · pytest · GitHub Actions

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
├── tests/                # Automated tests for core recommendation logic
├── .github/workflows/     # GitHub Actions CI workflow
├── requirements.txt      # Runtime Python dependencies
├── requirements-dev.txt  # Development/test dependencies
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

## Testing and CI

Automated tests cover core recommendation and discovery behavior. GitHub Actions runs the test suite on every push to `main` and on pull requests.

Run the tests locally with:

```bash
pip install -r requirements-dev.txt
pytest -q
```

The CI workflow also compiles the Python source before running the tests to catch syntax errors early.

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

## License

This project was created for academic and portfolio purposes. No open-source license has been added yet, so reuse is not automatically granted.
