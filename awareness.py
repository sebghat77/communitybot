from database import load_completed_profiles, save_nudge, log_event
from discovery import detect_interest_from_text


def normalize_text(text):
    return str(text or "").lower().strip()


def find_public_notify_channel(guild):
    # Keep #welcome clean for onboarding only.
    for name in ["events", "general"]:
        channel = next((c for c in guild.text_channels if c.name == name), None)
        if channel:
            return channel
    return None


def user_matches_interest(user, interest):
    interest = normalize_text(interest)
    persona = user.get("persona", {})

    interests = persona.get("interests", [])
    raw_interests = normalize_text(persona.get("raw_interests", ""))

    clean = [normalize_text(item) for item in interests]

    return interest in clean or interest in raw_interests


def get_users_by_interest(interest, limit=50):
    users = load_completed_profiles()
    relevant = []
    irrelevant = []

    for user in users:
        if user_matches_interest(user, interest):
            relevant.append(user)
        else:
            irrelevant.append(user)

    return relevant[:limit], irrelevant[:limit]


def get_teammate_matches(target_user_id, limit=5):
    users = load_completed_profiles()
    target = None

    for user in users:
        if str(user["user_id"]) == str(target_user_id):
            target = user
            break

    if target is None:
        return []

    target_persona = target.get("persona", {})
    target_interests = set(normalize_text(item) for item in target_persona.get("interests", []))
    target_goal = normalize_text(target_persona.get("goal", ""))

    if not target_interests:
        return []

    matches = []

    for user in users:
        if str(user["user_id"]) == str(target_user_id):
            continue

        persona = user.get("persona", {})
        interests = set(normalize_text(item) for item in persona.get("interests", []))
        shared = target_interests.intersection(interests)

        if not shared:
            continue

        score = len(shared)

        if target_goal and normalize_text(persona.get("goal", "")) == target_goal:
            score += 1

        if normalize_text(persona.get("goal", "")) == "teammates":
            score += 1

        matches.append({
            "user_id": user["user_id"],
            "username": user["username"],
            "shared_interests": list(shared),
            "score": score,
            "goal": persona.get("goal", "not provided"),
            "experience": persona.get("experience", "not provided")
        })

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:limit]


async def send_relevance_report(guild, title, detected_interest, relevant_users, irrelevant_users):
    log_channel = next((c for c in guild.text_channels if c.name == "bot-logs"), None)

    if not log_channel:
        return

    message = f"**{title}**\n\nDetected interest: `{detected_interest}`\n\n"

    message += "**Relevant users notified:**\n"
    if relevant_users:
        for user in relevant_users[:20]:
            message += f"- `{user['username']}`\n"
    else:
        message += "- none\n"

    message += "\n**Not relevant users:**\n"
    if irrelevant_users:
        for user in irrelevant_users[:20]:
            persona = user.get("persona", {})
            interests = ", ".join(persona.get("interests", [])) or "not provided"
            message += f"- `{user['username']}` — interests: `{interests}`\n"
    else:
        message += "- none\n"

    await log_channel.send(message[:1900])


async def automatic_event_nudge(guild, event_title, event_description=""):
    interest = detect_interest_from_text(f"{event_title} {event_description}")

    if interest is None:
        await send_relevance_report(guild, f"New event detected: {event_title}", "not detected", [], load_completed_profiles())
        return

    relevant_users, irrelevant_users = get_users_by_interest(interest)

    for user in relevant_users:
        member = guild.get_member(int(user["user_id"]))
        if not member:
            continue

        save_nudge(member.id, member.name, "real_event_notification", interest, event_title)

        try:
            await member.send(
                f"🎮 **Recommended for you**\n\n"
                f"A new event may interest you:\n"
                f"**{event_title}**\n\n"
                f"I sent this because it matches your interests."
            )
        except Exception:
            pass

    await send_relevance_report(guild, f"Automatic Event Awareness: {event_title}", interest, relevant_users, irrelevant_users)


async def automatic_channel_nudge(guild, channel_name, channel_mention):
    interest = detect_interest_from_text(channel_name)

    if interest is None:
        await send_relevance_report(guild, f"New channel detected: {channel_name}", "not detected", [], load_completed_profiles())
        return

    relevant_users, irrelevant_users = get_users_by_interest(interest)

    for user in relevant_users:
        member = guild.get_member(int(user["user_id"]))
        if not member:
            continue

        save_nudge(member.id, member.name, "real_channel_notification", interest, channel_name)

        try:
            await member.send(
                f"📢 **Recommended for you**\n\n"
                f"A new channel may be useful for you:\n"
                f"{channel_mention}\n\n"
                f"I sent this because it matches your interests."
            )
        except Exception:
            pass

    await send_relevance_report(guild, f"Automatic Channel Awareness: {channel_name}", interest, relevant_users, irrelevant_users)


async def manual_event_nudge(ctx, interest, event_title):
    relevant_users, irrelevant_users = get_users_by_interest(interest)

    for user in relevant_users:
        member = ctx.guild.get_member(int(user["user_id"]))
        if not member:
            continue

        save_nudge(member.id, member.name, "manual_event_notification", interest, event_title)

        try:
            await member.send(
                f"🎮 **Event nudge**\n\n"
                f"**{event_title}** may interest you because your profile matches `{interest}`."
            )
        except Exception:
            pass

    await send_relevance_report(ctx.guild, f"Manual Event Nudge: {event_title}", interest, relevant_users, irrelevant_users)
    await ctx.send("Event nudge processed. Report sent to #bot-logs.")


async def manual_channel_nudge(ctx, interest, target_channel):
    relevant_users, irrelevant_users = get_users_by_interest(interest)

    for user in relevant_users:
        member = ctx.guild.get_member(int(user["user_id"]))
        if not member:
            continue

        save_nudge(member.id, member.name, "manual_channel_notification", interest, target_channel.name)

        try:
            await member.send(
                f"📢 **Channel nudge**\n\n"
                f"{target_channel.mention} may be useful for you because your profile matches `{interest}`."
            )
        except Exception:
            pass

    await send_relevance_report(ctx.guild, f"Manual Channel Nudge: {target_channel.name}", interest, relevant_users, irrelevant_users)
    await ctx.send("Channel nudge processed. Report sent to #bot-logs.")


async def send_teammate_suggestions_to(channel, guild, target_member):
    matches = get_teammate_matches(str(target_member.id))

    if not matches:
        await channel.send(f"I could not find teammate suggestions for {target_member.mention} yet.")
        return

    lines = []

    for match in matches:
        member = guild.get_member(int(match["user_id"]))
        if member:
            shared = ", ".join(match["shared_interests"])
            lines.append(f"- {member.mention} — shared interests: `{shared}`, goal: `{match['goal']}`")

    if not lines:
        await channel.send("Possible matches are not available in this server.")
        return

    log_event(target_member.id, str(target_member), "teammate_suggestions_shown", str(len(lines)))

    await channel.send(
        "**Friend / Teammate Suggestions**\n\n"
        f"For: {target_member.mention}\n\n"
        + "\n".join(lines)
        + "\n\nThese suggestions are based on shared onboarding interests."
    )


async def teammate_nudge(ctx, target_member):
    await send_teammate_suggestions_to(ctx.channel, ctx.guild, target_member)
