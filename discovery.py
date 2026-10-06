import re

from config import DISCOVERABLE_CATEGORIES, IGNORED_CHANNEL_KEYWORDS, INTEREST_KEYWORDS, CHANNEL_FALLBACK_MAP


def normalize(text):
    return str(text or "").lower().replace("_", "-").strip()


def contains_keyword(text, keyword):
    text = normalize(text)
    keyword = normalize(keyword)

    if not keyword:
        return False

    pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def is_ignored_channel(channel):
    name = normalize(channel.name)
    return any(word in name for word in IGNORED_CHANNEL_KEYWORDS)


def is_discoverable_category(category_name):
    allowed = [item.upper() for item in DISCOVERABLE_CATEGORIES]
    return str(category_name or "").upper() in allowed


def get_discoverable_channels(guild):
    channels = []

    for channel in guild.text_channels:
        if is_ignored_channel(channel):
            continue

        if channel.category is None:
            continue

        if not is_discoverable_category(channel.category.name):
            continue

        channels.append(channel)

    return channels


def detect_interest_from_text(text):
    text = normalize(text)

    for interest, keywords in INTEREST_KEYWORDS.items():
        for keyword in keywords:
            if contains_keyword(text, keyword):
                return interest

    return None


def channel_matches_interest(channel, interest):
    interest = normalize(interest)
    name = normalize(channel.name)
    topic = normalize(getattr(channel, "topic", ""))

    keywords = INTEREST_KEYWORDS.get(interest, [interest])

    if contains_keyword(name, interest) or contains_keyword(topic, interest):
        return True

    return any(
        contains_keyword(name, keyword) or contains_keyword(topic, keyword)
        for keyword in keywords
    )


def get_dynamic_recommendations(guild, persona):
    channels = get_discoverable_channels(guild)
    interests = persona.get("interests", [])
    goal = persona.get("goal", "not provided")

    recommendations = []

    for channel in channels:
        reasons = []

        for interest in interests:
            if channel_matches_interest(channel, interest):
                reasons.append(f"matches your interest in {interest}")

        name = normalize(channel.name)

        if goal == "teammates" and ("team" in name or "squad" in name):
            reasons.append("matches your goal of finding teammates")

        if goal == "events" and "event" in name:
            reasons.append("matches your goal of joining events")

        if goal == "help" and "help" in name:
            reasons.append("matches your goal of getting help")

        if reasons:
            recommendations.append((channel.name, "; ".join(reasons)))

    if not recommendations:
        for interest in interests:
            for channel_name in CHANNEL_FALLBACK_MAP.get(interest, []):
                recommendations.append((channel_name, f"matches your interest in {interest}"))

    for basic in ["general", "introductions"]:
        if not any(item[0] == basic for item in recommendations):
            recommendations.insert(0, (basic, "good starting point for community participation"))

    clean = []
    seen = set()

    for channel_name, reason in recommendations:
        if channel_name not in seen:
            clean.append((channel_name, reason))
            seen.add(channel_name)

    return clean[:8]
