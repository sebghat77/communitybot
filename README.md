# CommunityBot Final v3

Final integrated Discord bot for the Cooperation Systems project.

## Run

```powershell
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

Add fresh tokens to `.env`.

## First commands in Discord

```text
!setup_server
!join
!project_help
```

## Evaluation

```text
!evaluation_summary
!community_status
!recent_logs 10
```

Admin reports are sent to `#bot-logs`.

## Dashboard

```powershell
python dashboard.py
```

Open `http://127.0.0.1:5000`.

## Export

```powershell
python export_evaluation.py
```


## Fresh clean server setup

If your server has many old test channels, run:

```text
!fresh_setup CONFIRM
```

This deletes old channels/categories and rebuilds the clean project structure. Use it only in a test/project server.

## 24/7 hosting

The bot only works while `python bot.py` is running. If your laptop is off, the bot is offline.

For 24/7 access, deploy it to a host such as Railway, Render, Fly.io, Replit, or a VPS. Add these environment variables on the host:

```text
DISCORD_TOKEN
MISTRAL_API_KEY
BOT_NAME
```

Start command:

```text
python bot.py
```


## v5 changes

- `#onboarding` is no longer needed. Welcome + onboarding happen in `#welcome`.
- User sees onboarding steps privately after clicking the button.
- Non-onboarded users are guided to `#welcome`.
- Notifications are sent by DM and also mention the user in `#events`, `#welcome`, or `#general`.
- Discord pop-up behavior still depends on the user's own Discord notification settings.


## v6 changes

- Onboarding is sent in `#welcome` and also directly in DM.
- `#welcome` stays clean for onboarding only.
- Event/channel notifications are posted in `#events` or `#general`, not in `#welcome`.


## v7 changes

- `#welcome` contains only the static Start Onboarding entry point.
- Each user gets private onboarding in DM after clicking Start Onboarding.
- If a non-onboarded user writes elsewhere, the bot only replies with a short guidance message and sends onboarding to DM.
- The virtual evaluation flow now sends two recommendations:
  1. a suggested channel idea,
  2. an event idea after 60 seconds.
- Both virtual recommendations are sent in DM and mentioned in `#events` or `#general`.
- `#welcome` is not used for event/channel notifications.


## v8 changes

- Each new user gets a private onboarding channel named like `welcome-username-1234`.
- Only that user, the bot, and admins can see the private onboarding channel.
- If a non-onboarded user writes anywhere else, the bot directs them to their private onboarding channel.
- Onboarding happens inside that private channel, not in public `#welcome`.
- After onboarding is completed, the private onboarding channel is deleted automatically after about 90 seconds.
- Admins can still see private onboarding channels for support/debugging.


## v9 changes

- Virtual recommendations are DM-only.
- Real event/channel notifications are DM-only.
- No notification is posted in `#events`, `#general`, or `#welcome`.
- This prevents other users from clicking another user's notification.
- Admin visibility remains available through `#bot-logs`.
- To make new users land on `#welcome`, create/copy the server invite from the `#welcome` channel.
