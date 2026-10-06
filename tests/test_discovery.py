from types import SimpleNamespace

from discovery import (
    channel_matches_interest,
    detect_interest_from_text,
    get_dynamic_recommendations,
    is_discoverable_category,
    normalize,
)


def make_channel(name, category="COMMUNITY", topic=""):
    category_obj = SimpleNamespace(name=category) if category is not None else None
    return SimpleNamespace(name=name, category=category_obj, topic=topic)


def make_guild(*channels):
    return SimpleNamespace(text_channels=list(channels))


def test_normalize_handles_none_spaces_and_underscores():
    assert normalize(None) == ""
    assert normalize("  Tech_Talk  ") == "tech-talk"


def test_detect_interest_from_text_finds_known_interest():
    assert detect_interest_from_text("I enjoy Valorant and FPS games") == "fps"
    assert detect_interest_from_text("I like Python and coding") == "tech"


def test_discoverable_category_is_case_insensitive():
    assert is_discoverable_category("community")
    assert is_discoverable_category("GAME DISCUSSIONS")
    assert not is_discoverable_category("START HERE")


def test_channel_matches_interest_uses_name_and_topic():
    tech = make_channel("general-dev", category="GAME DISCUSSIONS", topic="Python coding and hardware")
    fps = make_channel("fps-discussion", category="GAME DISCUSSIONS", topic="Shooter games")

    assert channel_matches_interest(tech, "tech")
    assert channel_matches_interest(fps, "fps")
    assert not channel_matches_interest(fps, "rpg")


def test_dynamic_recommendations_include_matching_and_basic_channels():
    guild = make_guild(
        make_channel("tech-talk", category="GAME DISCUSSIONS", topic="Python, hardware and bots"),
        make_channel("events", category="COMMUNITY", topic="Community tournaments and meetups"),
        make_channel("bot-logs", category="COMMUNITY", topic="Administrative logs"),
    )
    persona = {"interests": ["tech"], "goal": "events"}

    recommendations = get_dynamic_recommendations(guild, persona)
    names = [name for name, _ in recommendations]

    assert "tech-talk" in names
    assert "events" in names
    assert "bot-logs" not in names
    assert "general" in names
    assert "introductions" in names


def test_dynamic_recommendations_fall_back_when_no_live_match_exists():
    guild = make_guild(
        make_channel("general-chat", category="COMMUNITY", topic="General discussion"),
    )
    persona = {"interests": ["rpg"], "goal": "not provided"}

    recommendations = get_dynamic_recommendations(guild, persona)
    names = [name for name, _ in recommendations]

    assert "rpg-discussion" in names
