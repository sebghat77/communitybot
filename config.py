import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = os.getenv("BOT_NAME", "CommunityBot")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = "mistral-small-latest"
DB_NAME = "community.db"

ALLOWED_INTERESTS = ["fps", "rpg", "strategy", "casual", "tech", "events"]
ALLOWED_GOALS = ["teammates", "events", "discussion", "help", "not provided"]
ALLOWED_EXPERIENCE = ["beginner", "intermediate", "advanced", "not provided"]

DISCOVERABLE_CATEGORIES = [
    "COMMUNITY",
    "GAME DISCUSSIONS",
    "SUPPORT AND FEEDBACK"
]

IGNORED_CHANNEL_KEYWORDS = [
    "bot", "log", "logs", "test", "debug", "archive", "old",
    "backup", "rules", "welcome", "onboarding", "community-status",
    "feedback"
]

INTEREST_KEYWORDS = {
    "fps": ["fps", "shooter", "shooting", "pubg", "valorant", "cs2", "csgo", "counter", "cod", "call-of-duty", "apex", "squad"],
    "rpg": ["rpg", "roleplay", "role-play", "role", "quest", "fantasy", "elden", "skyrim", "story"],
    "strategy": ["strategy", "strategic", "tactic", "tactical", "chess", "planning", "civilization", "aoe"],
    "casual": ["casual", "chill", "relax", "relaxed", "fun", "social", "minecraft", "gta"],
    "tech": ["tech", "technology", "bot", "python", "coding", "setup", "tools", "hardware"],
    "events": ["event", "events", "tournament", "session", "meetup", "night", "competition"]
}

CHANNEL_FALLBACK_MAP = {
    "fps": ["fps-discussion", "looking-for-team"],
    "rpg": ["rpg-discussion"],
    "strategy": ["strategy-discussion"],
    "casual": ["casual-chat"],
    "tech": ["tech-talk"],
    "events": ["events"]
}

SERVER_CHANNELS = {
    "START HERE": [
        ("welcome", "Welcome and onboarding area for new members."),
        ("rules", "Community rules and participation guidelines."),
        ("introductions", "New members introduce themselves here.")
    ],
    "COMMUNITY": [
        ("general", "General community discussion."),
        ("events", "Events and announcements."),
        ("looking-for-team", "Find teammates and group members.")
    ],
    "GAME DISCUSSIONS": [
        ("fps-discussion", "FPS games such as PUBG, Valorant, CS2 and shooters."),
        ("rpg-discussion", "RPG and story-driven games."),
        ("strategy-discussion", "Strategy games and tactical discussions."),
        ("casual-chat", "Casual gaming and relaxed conversation."),
        ("tech-talk", "Technology, tools, setups and bots.")
    ],
    "SUPPORT AND FEEDBACK": [
        ("help", "Ask for help."),
        ("feedback", "Give feedback about the community and bot.")
    ],
    "COMMUNITY AWARENESS": [
        ("community-status", "Community health reports."),
        ("bot-logs", "Bot logs and awareness messages.")
    ]
}
