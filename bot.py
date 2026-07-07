import asyncio
import re
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, SERVER_CHANNELS
from database import (
    init_db, create_or_touch_user, save_persona, get_persona, log_event,
    log_message_activity, save_recommendation, save_nudge, mark_nudge_engaged,
    get_channel_activity, get_user_activity, get_user_activity_by_channel,
    get_recommendation_stats, get_nudge_stats, get_event_counts,
    get_recent_logs, get_evaluation_summary
)
from discovery import get_dynamic_recommendations
from llm import create_persona_with_llm, explain_recommendations_with_llm, community_assistant_answer, generate_discussion_prompt
import awareness

init_db()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guild_scheduled_events = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def lock_private_channels(guild):
    """Make admin/evaluation channels private."""
    for name in ["bot-logs", "community-status"]:
        channel = find_channel(guild, name)
        if channel:
            await channel.set_permissions(guild.default_role, view_channel=False)
            await channel.set_permissions(guild.me, view_channel=True, send_messages=True, read_message_history=True)


async def delete_project_channels_and_categories(guild):
    """Admin reset: removes all current channels/categories, then setup_server rebuilds structure."""
    for channel in list(guild.channels):
        try:
            await channel.delete(reason="CommunityBot fresh setup")
        except Exception:
            pass




def is_admin(member):
    return bool(getattr(member, "guild_permissions", None) and member.guild_permissions.administrator)


def find_channel(guild, channel_name):
    return discord.utils.get(guild.text_channels, name=channel_name)


def bot_logs_channel(guild):
    return find_channel(guild, "bot-logs")


def public_recommendation_channel(guild):
    return find_channel(guild, "events") or find_channel(guild, "general")


def safe_channel_name(name):
    cleaned = str(name or "user").lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned[:40] or "user"


async def get_private_welcome_channel(guild, member):
    """Create or return a private onboarding channel for one user."""
    channel_name = f"welcome-{safe_channel_name(member.name)}-{str(member.id)[-4:]}"
    existing = find_channel(guild, channel_name)
    if existing:
        return existing

    category = discord.utils.get(guild.categories, name="PRIVATE ONBOARDING")
    if category is None:
        category = await guild.create_category(name="PRIVATE ONBOARDING")
        await category.set_permissions(guild.default_role, view_channel=False)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=False
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True
        )
    }

    channel = await guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites,
        topic=f"Private onboarding channel for {member}."
    )

    return channel


async def delete_private_welcome_later(channel, seconds=90):
    """Delete private onboarding channel after a short delay."""
    if not channel or not getattr(channel, "name", "").startswith("welcome-"):
        return

    await asyncio.sleep(seconds)
    try:
        await channel.delete(reason="Onboarding completed")
    except Exception:
        pass



def channel_mention(guild, channel_name):
    channel = find_channel(guild, channel_name)
    return channel.mention if channel else f"#{channel_name}"


async def send_long_message(channel, text):
    if len(text) <= 1900:
        await channel.send(text)
        return

    for i in range(0, len(text), 1900):
        await channel.send(text[i:i + 1900])


async def send_admin_report(ctx, report):
    if not is_admin(ctx.author):
        await ctx.send("This command is only available for admins.")
        return

    log_channel = bot_logs_channel(ctx.guild)

    if log_channel:
        await send_long_message(log_channel, report)
        if ctx.channel != log_channel:
            await ctx.send("Admin report sent to #bot-logs.")
    else:
        await send_long_message(ctx.channel, report)


def build_welcome_embed():
    embed = discord.Embed(
        title="Welcome to CommunityBot",
        description=(
            "I help you enter the community without getting lost.\n\n"
            "Start onboarding, choose your interests, and I will recommend channels and people."
        ),
        color=discord.Color.blue()
    )

    embed.add_field(
        name="What I support",
        value=(
            "• Smart onboarding\n"
            "• Channel recommendations\n"
            "• Friend / teammate suggestions\n"
            "• Event and channel nudges\n"
            "• Community activity monitoring"
        ),
        inline=False
    )

    return embed


def build_profile_embed(username, persona, recommendations, guild):
    interests = persona.get("interests", [])
    interest_text = ", ".join(interests) if interests else "not provided"

    rec_text = ""
    for channel_name, reason in recommendations:
        rec_text += f"• {channel_mention(guild, channel_name)} — {reason}\n"

    embed = discord.Embed(
        title="Your community profile is ready",
        description="I used your onboarding answers to create this profile.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Profile",
        value=(
            f"Username: `{username}`\n"
            f"Interests: `{interest_text}`\n"
            f"Goal: `{persona.get('goal', 'not provided')}`\n"
            f"Experience: `{persona.get('experience', 'not provided')}`\n"
            f"Preferences: `{persona.get('preferences', 'not provided')}`"
        ),
        inline=False
    )

    embed.add_field(
        name="Recommended channels",
        value=rec_text or "No recommendations yet.",
        inline=False
    )

    embed.add_field(
        name="Next step",
        value="Open a recommended channel and send a short message.",
        inline=False
    )

    return embed


async def send_profile(channel, guild, user):
    data = get_persona(str(user.id))

    if data is None or data["onboarding_completed"] == 0:
        await channel.send(f"{user.mention}, you do not have a profile yet. Please use onboarding first.")
        return

    recommendations = get_dynamic_recommendations(guild, data["persona"])
    await channel.send(
        content=user.mention,
        embed=build_profile_embed(str(user), data["persona"], recommendations, guild),
        view=AfterOnboardingView()
    )


async def send_recommendations(channel, guild, user, use_llm=True):
    user_id = str(user.id)
    data = get_persona(user_id)

    if data is None or data["onboarding_completed"] == 0:
        await channel.send(f"{user.mention}, please complete onboarding first.")
        return

    persona = data["persona"]
    recommendations = get_dynamic_recommendations(guild, persona)

    for channel_name, reason in recommendations:
        save_recommendation(user_id, str(user), channel_name, reason)

    embed = build_profile_embed(str(user), persona, recommendations, guild)
    await channel.send(content=user.mention, embed=embed, view=AfterOnboardingView())

    if not use_llm:
        return

    channels_text = ""
    for channel_name, reason in recommendations:
        channels_text += f"- #{channel_name}: {reason}\n"

    await channel.send("Creating a short AI explanation...")

    answer = await asyncio.to_thread(explain_recommendations_with_llm, persona, channels_text)
    await send_long_message(channel, answer)



class InterestButton(discord.ui.Button):
    def __init__(self, label, value, emoji=None):
        super().__init__(label=label, style=discord.ButtonStyle.primary, emoji=emoji)
        self.value = value

    async def callback(self, interaction):
        log_event(interaction.user.id, str(interaction.user), "interest_selected_quick", self.value)
        await interaction.response.send_message(
            "**Step 2/3:** Now choose your experience level:",
            view=ExperienceSelectView(self.value),
            ephemeral=True
        )


class InterestSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(InterestButton("FPS / Shooter", "fps", "🎮"))
        self.add_item(InterestButton("RPG", "rpg", "🧙"))
        self.add_item(InterestButton("Strategy", "strategy", "♟️"))
        self.add_item(InterestButton("Casual", "casual", "💬"))
        self.add_item(InterestButton("Tech", "tech", "🛠️"))
        self.add_item(InterestButton("Events", "events", "🏆"))


class ExperienceButton(discord.ui.Button):
    def __init__(self, label, value, interests):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.value = value
        self.interests = interests

    async def callback(self, interaction):
        log_event(interaction.user.id, str(interaction.user), "experience_selected", self.value)
        await interaction.response.send_modal(
            SmartOnboardingModal(
                prefilled_interests=self.interests,
                prefilled_experience=self.value
            )
        )


class ExperienceSelectView(discord.ui.View):
    def __init__(self, interests):
        super().__init__(timeout=300)
        self.add_item(ExperienceButton("Beginner", "beginner", interests))
        self.add_item(ExperienceButton("Intermediate", "intermediate", interests))
        self.add_item(ExperienceButton("Advanced", "advanced", interests))


class SmartOnboardingModal(discord.ui.Modal, title="Final Onboarding Step"):
    goal = discord.ui.TextInput(
        label="What do you want to do here?",
        placeholder="Example: find teammates, join events, discuss, get help",
        max_length=150
    )

    preferences = discord.ui.TextInput(
        label="Any preference?",
        placeholder="Example: beginner friendly, casual teammates",
        required=False,
        max_length=150
    )

    def __init__(self, prefilled_interests="", prefilled_experience="not provided"):
        super().__init__()
        self.prefilled_interests = prefilled_interests
        self.prefilled_experience = prefilled_experience

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        user_id = str(interaction.user.id)
        username = str(interaction.user)

        create_or_touch_user(user_id, username)

        persona = await asyncio.to_thread(
            create_persona_with_llm,
            self.prefilled_interests,
            str(self.goal.value),
            self.prefilled_experience,
            str(self.preferences.value)
        )

        save_persona(user_id, username, persona)

        recommendations = get_dynamic_recommendations(interaction.guild, persona)

        for channel_name, reason in recommendations:
            save_recommendation(user_id, username, channel_name, reason)

        embed = build_profile_embed(username, persona, recommendations, interaction.guild)

        await interaction.followup.send(
            embed=embed,
            view=AfterOnboardingView()
        )

        if interaction.guild and getattr(interaction.channel, "name", "").startswith("welcome-"):
            await interaction.followup.send(
                "✅ Onboarding completed. This private onboarding channel will be deleted soon. "
                "You can continue through recommendations and notifications in DM or normal community channels."
            )
            asyncio.create_task(delete_private_welcome_later(interaction.channel, 90))

        await send_virtual_evaluation_nudge(interaction.guild, interaction.user, persona)


class StartOnboardingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Start Onboarding", style=discord.ButtonStyle.primary)
    async def start_onboarding(self, interaction: discord.Interaction, button: discord.ui.Button):
        create_or_touch_user(interaction.user.id, str(interaction.user))
        log_event(interaction.user.id, str(interaction.user), "onboarding_started")

        # If the user clicked inside their private welcome channel, continue there.
        if interaction.guild and getattr(interaction.channel, "name", "").startswith("welcome-"):
            await interaction.response.send_message(
                "👋 Great! This onboarding is private and only visible to you and admins.\n\n"
                "**Step 1/3:** Choose your main interests:",
                view=InterestSelectView()
            )
            return

        # Otherwise create/find a private welcome channel for this user.
        if interaction.guild:
            private_channel = await get_private_welcome_channel(interaction.guild, interaction.user)
            await private_channel.send(
                f"{interaction.user.mention} 👋 This is your private onboarding channel.\n\n"
                "**Step 1/3:** Choose your main interests:",
                view=InterestSelectView(),
                allowed_mentions=discord.AllowedMentions(users=True)
            )
            await interaction.response.send_message(
                f"I created your private onboarding channel: {private_channel.mention}",
                ephemeral=True
            )
            return

        # Fallback for DM usage.
        await interaction.response.send_message(
            "👋 Great! **Step 1/3:** Choose your main interests:",
            view=InterestSelectView()
        )


class IntroductionModal(discord.ui.Modal, title="Post Introduction"):
    intro = discord.ui.TextInput(
        label="Your short introduction",
        placeholder="Example: Hi, I am new here. I like FPS games.",
        style=discord.TextStyle.paragraph,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = find_channel(interaction.guild, "introductions")

        if channel is None:
            await interaction.response.send_message("I could not find #introductions.", ephemeral=True)
            return

        await channel.send(f"Introduction from {interaction.user.mention}:\n\n{self.intro.value}")

        log_event(interaction.user.id, str(interaction.user), "introduction_posted", str(self.intro.value), str(channel.id), channel.name)
        await interaction.response.send_message("Your introduction has been posted.", ephemeral=True)


class AfterOnboardingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="View Profile", style=discord.ButtonStyle.secondary)
    async def view_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_event(interaction.user.id, str(interaction.user), "view_profile_clicked")
        await interaction.response.defer()
        await send_profile(interaction.channel, interaction.guild, interaction.user)

    @discord.ui.button(label="Recommend Channels", style=discord.ButtonStyle.primary)
    async def recommend_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_event(interaction.user.id, str(interaction.user), "recommend_again_clicked")
        await interaction.response.defer()
        await send_recommendations(interaction.channel, interaction.guild, interaction.user, True)

    @discord.ui.button(label="Find Teammates", style=discord.ButtonStyle.success)
    async def find_teammates(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_event(interaction.user.id, str(interaction.user), "find_teammates_clicked")
        await interaction.response.defer()
        await awareness.send_teammate_suggestions_to(interaction.channel, interaction.guild, interaction.user)

    @discord.ui.button(label="Post Introduction", style=discord.ButtonStyle.secondary)
    async def post_intro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(IntroductionModal())


class EvaluationNudgeView(discord.ui.View):
    def __init__(self, target):
        super().__init__(timeout=600)
        self.target = target

    @discord.ui.button(label="Interested", style=discord.ButtonStyle.success)
    async def interested(self, interaction: discord.Interaction, button: discord.ui.Button):
        mark_nudge_engaged(interaction.user.id, str(interaction.user), self.target)
        await interaction.response.send_message("Thanks! I will remember that this kind of recommendation is useful for you.", ephemeral=True)

    @discord.ui.button(label="Not Interested", style=discord.ButtonStyle.secondary)
    async def not_interested(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_event(interaction.user.id, str(interaction.user), "evaluation_nudge_not_interested", self.target)
        await interaction.response.send_message("Thanks! I will send fewer recommendations like this.", ephemeral=True)




async def send_virtual_evaluation_nudge(guild, user, persona):
    interests = persona.get("interests", [])
    interest = interests[0] if interests else "community"

    async def send_one(kind, title, description):
        target = title
        save_nudge(user.id, str(user), kind, interest, target)

        message = (
            f"🎯 **Recommended for you**\n\n"
            f"{description}\n\n"
            f"**{target}**\n\n"
            f"Would you be interested?"
        )

        # DM only. No public channel message, so other users cannot click another user's notification.
        try:
            await user.send(message, view=EvaluationNudgeView(target))
        except Exception:
            private_channel = await get_private_welcome_channel(guild, user)
            await private_channel.send(
                f"{user.mention}\n{message}",
                view=EvaluationNudgeView(target),
                allowed_mentions=discord.AllowedMentions(users=True)
            )

        relevant_users, irrelevant_users = awareness.get_users_by_interest(interest)
        await awareness.send_relevance_report(
            guild,
            f"Evaluation Recommendation: {target}",
            interest,
            relevant_users,
            irrelevant_users
        )

    # First: suggested channel idea
    await send_one(
        "virtual_channel_recommendation",
        f"Create a new {interest.upper()} channel",
        "Based on your profile, a focused channel like this could help you find relevant discussions faster."
    )

    # Second: event idea after short delay. In a real long-term evaluation this can be 30 minutes.
    await asyncio.sleep(60)
    await send_one(
        "virtual_event_recommendation",
        f"{interest.upper()} Community Night",
        "Based on your profile, this event could help you participate and meet similar members."
    )


async def get_or_create_category(guild, category_name):
    category = discord.utils.get(guild.categories, name=category_name)
    if category:
        return category
    return await guild.create_category(name=category_name)


async def get_or_create_text_channel(guild, channel_name, category=None, topic=None):
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel:
        return channel
    return await guild.create_text_channel(name=channel_name, category=category, topic=topic)


async def send_onboarding_to_member(member):
    # Create a private welcome/onboarding channel for this user.
    private_channel = await get_private_welcome_channel(member.guild, member)

    await private_channel.send(
        f"{member.mention} 👋 Welcome! This private channel is only for your onboarding.\n\n"
        "Please press **Start Onboarding** below.",
        embed=build_welcome_embed(),
        view=StartOnboardingView(),
        allowed_mentions=discord.AllowedMentions(users=True)
    )

    try:
        await member.send(
            f"Welcome! I created your private onboarding channel in the server: {private_channel.mention}"
        )
    except Exception:
        pass


@bot.event
async def on_ready():
    init_db()
    print(f"Bot is online as {bot.user}")


@bot.event
async def on_member_join(member):
    create_or_touch_user(str(member.id), str(member))
    log_event(member.id, str(member), "user_joined")
    await send_onboarding_to_member(member)


@bot.event
async def on_scheduled_event_create(event):
    description = event.description if event.description else ""
    log_event(event.creator_id if event.creator_id else "", "scheduled_event", "event_created", event.name)
    await awareness.automatic_event_nudge(guild=event.guild, event_title=event.name, event_description=description)


@bot.event
async def on_guild_channel_create(channel):
    if not isinstance(channel, discord.TextChannel):
        return

    log_event("", "system", "channel_created", channel.name, channel.id, channel.name)
    await awareness.automatic_channel_nudge(guild=channel.guild, channel_name=channel.name, channel_mention=channel.mention)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    username = str(message.author)

    if isinstance(message.channel, discord.DMChannel):
        channel_name = "Direct Message"
        guild = message.guild
    else:
        channel_name = str(message.channel.name)
        guild = message.guild

    log_message_activity(user_id=user_id, username=username, channel_id=str(message.channel.id), channel_name=channel_name, content=message.content)

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    text = message.content.lower()
    data = get_persona(user_id)
    persona = data["persona"] if data and data["onboarding_completed"] == 1 else None

    if guild and ("show my profile" in text or "my profile" in text or text.strip() == "profile"):
        await send_profile(message.channel, guild, message.author)
        return

    if guild and ("recommend" in text or "which channel" in text or "where should i go" in text):
        await send_recommendations(message.channel, guild, message.author, True)
        return

    if guild and ("teammate" in text or "friend" in text or "squad" in text):
        await awareness.send_teammate_suggestions_to(message.channel, guild, message.author)
        return

    if persona is None and guild:
        private_channel = await get_private_welcome_channel(guild, message.author)

        # Make sure the private channel has a start button if it is empty/new.
        await private_channel.send(
            f"{message.author.mention}, please complete onboarding here so I can guide you properly.",
            embed=build_welcome_embed(),
            view=StartOnboardingView(),
            allowed_mentions=discord.AllowedMentions(users=True)
        )

        await message.reply(
            f"Please complete onboarding first in your private channel: {private_channel.mention}",
            mention_author=True
        )
        return

    await message.channel.send("Thinking...")

    answer = await asyncio.to_thread(community_assistant_answer, message.content, persona)
    await send_long_message(message.channel, answer)

    await bot.process_commands(message)


@bot.command()
async def ping(ctx):
    await ctx.send("pong" if is_admin(ctx.author) else "Bot is online.")


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_server(ctx):
    await ctx.send("Creating server structure...")

    for category_name, channels in SERVER_CHANNELS.items():
        category = await get_or_create_category(ctx.guild, category_name)

        for channel_name, topic in channels:
            await get_or_create_text_channel(ctx.guild, channel_name, category, topic)

    await lock_private_channels(ctx.guild)
    await ctx.send("Server setup completed. Use `!join` or go to #welcome.")



@bot.command()
@commands.has_permissions(administrator=True)
async def fresh_setup(ctx, confirmation: str = ""):
    if confirmation != "CONFIRM":
        await ctx.send(
            "This will delete all current server channels/categories and rebuild a clean project structure.\n"
            "Run: `!fresh_setup CONFIRM`"
        )
        return

    await ctx.send("Fresh setup started. Deleting old channels and rebuilding clean structure...")
    await delete_project_channels_and_categories(ctx.guild)

    for category_name, channels in SERVER_CHANNELS.items():
        category = await get_or_create_category(ctx.guild, category_name)
        for channel_name, topic in channels:
            await get_or_create_text_channel(ctx.guild, channel_name, category, topic)

    await lock_private_channels(ctx.guild)

    welcome = find_channel(ctx.guild, "welcome")
    if welcome:
        await welcome.send(embed=build_welcome_embed(), view=StartOnboardingView())


@bot.command()
async def join(ctx):
    create_or_touch_user(str(ctx.author.id), str(ctx.author))
    log_event(ctx.author.id, str(ctx.author), "join_command_used")

    private_channel = await get_private_welcome_channel(ctx.guild, ctx.author)
    await private_channel.send(
        f"{ctx.author.mention}, start your private onboarding here:",
        embed=build_welcome_embed(),
        view=StartOnboardingView(),
        allowed_mentions=discord.AllowedMentions(users=True)
    )

    await ctx.send(f"{ctx.author.mention}, I created your private onboarding channel: {private_channel.mention}")


@bot.command()
async def profile(ctx):
    await send_profile(ctx.channel, ctx.guild, ctx.author)


@bot.command()
async def recommend(ctx):
    await send_recommendations(ctx.channel, ctx.guild, ctx.author, False)


@bot.command()
async def ai_recommend(ctx):
    await send_recommendations(ctx.channel, ctx.guild, ctx.author, True)


@bot.command()
async def ask(ctx, *, question):
    data = get_persona(str(ctx.author.id))
    persona = data["persona"] if data and data["onboarding_completed"] == 1 else None

    await ctx.send("Thinking...")
    answer = await asyncio.to_thread(community_assistant_answer, question, persona)
    await send_long_message(ctx.channel, answer)


@bot.command()
async def generate_prompt(ctx, channel: discord.TextChannel = None):
    if channel is None:
        await ctx.send("Use: `!generate_prompt #channel-name`")
        return

    answer = await asyncio.to_thread(generate_discussion_prompt, channel.name)
    await ctx.send(f"Suggested prompt for {channel.mention}:\n\n{answer}")


@bot.command()
async def event_nudge(ctx, interest: str, *, event_title: str):
    if not is_admin(ctx.author):
        await ctx.send("Only admins can use this command.")
        return
    await awareness.manual_event_nudge(ctx, interest, event_title)


@bot.command()
async def channel_nudge(ctx, interest: str, channel: discord.TextChannel):
    if not is_admin(ctx.author):
        await ctx.send("Only admins can use this command.")
        return
    await awareness.manual_channel_nudge(ctx, interest, channel)


@bot.command()
async def teammate_nudge(ctx, member: discord.Member = None):
    target = member if member else ctx.author

    if target != ctx.author and not is_admin(ctx.author):
        await ctx.send("You can only request teammate suggestions for yourself.")
        return

    await awareness.send_teammate_suggestions_to(ctx.channel, ctx.guild, target)


@bot.command()
async def community_status(ctx):
    channel_activity = get_channel_activity()
    user_activity = get_user_activity(5)
    recommendation_stats = get_recommendation_stats()
    nudge_stats = get_nudge_stats()
    summary = get_evaluation_summary()

    report = "**Community Health Report**\n\n"
    report += "**Evaluation summary:**\n"
    report += f"- Users total: `{summary['users_total']}`\n"
    report += f"- Onboarding completed: `{summary['onboarding_completed']}`\n"
    report += f"- Onboarding rate: `{summary['onboarding_rate']}%`\n"
    report += f"- Recommendations sent: `{summary['recommendations_sent']}`\n"
    report += f"- Recommendations engaged: `{summary['recommendations_engaged']}`\n"
    report += f"- Recommendation engagement rate: `{summary['recommendation_engagement_rate']}%`\n"
    report += f"- Nudges sent: `{summary['nudges_sent']}`\n"
    report += f"- Nudges engaged: `{summary['nudges_engaged']}`\n"
    report += f"- Nudge engagement rate: `{summary['nudge_engagement_rate']}%`\n"
    report += f"- Messages logged: `{summary['messages_logged']}`\n\n"

    report += "**Most active channels:**\n"
    if channel_activity:
        for channel_name, count in channel_activity[:5]:
            report += f"- `#{channel_name}`: `{count}` messages\n"
    else:
        report += "- No channel activity yet\n"

    report += "\n**Most active users:**\n"
    if user_activity:
        for username, count in user_activity:
            report += f"- `{username}`: `{count}` messages\n"
    else:
        report += "- No user activity yet\n"

    report += "\n**Recommendation engagement:**\n"
    if recommendation_stats:
        for status, count in recommendation_stats:
            report += f"- `{status}`: `{count}`\n"
    else:
        report += "- No recommendation data yet\n"

    report += "\n**Nudge types:**\n"
    if nudge_stats:
        for nudge_type, status, count in nudge_stats:
            report += f"- `{nudge_type}` / `{status}`: `{count}`\n"
    else:
        report += "- No nudge data yet\n"

    await send_admin_report(ctx, report)


@bot.command()
async def evaluation_summary(ctx):
    summary = get_evaluation_summary()
    event_counts = get_event_counts()

    report = "**Evaluation Data Summary**\n\n"
    for key, value in summary.items():
        report += f"- `{key}`: `{value}`\n"

    report += "\n**Logged event types:**\n"
    for event_type, count in event_counts:
        report += f"- `{event_type}`: `{count}`\n"

    await send_admin_report(ctx, report)


@bot.command()
async def leader_candidates(ctx, channel: discord.TextChannel = None):
    if channel is None:
        users = get_user_activity(10)
        title = "Potential community contributors based on overall participation"
    else:
        users = get_user_activity_by_channel(channel.name, 10)
        title = f"Potential community contributors in #{channel.name}"

    if not users:
        await ctx.send("No activity data yet.")
        return

    response = f"**{title}**\n\n"

    for index, (username, count) in enumerate(users, start=1):
        response += f"{index}. `{username}` — `{count}` messages\n"

    response += "\nThis is not automatic moderator selection. It only supports system awareness for community management."
    await send_admin_report(ctx, response)


@bot.command()
async def recent_logs(ctx, limit: int = 10):
    if limit > 20:
        limit = 20

    rows = get_recent_logs(limit)
    if not rows:
        await ctx.send("No logs yet.")
        return

    response = "**Recent Logs**\n\n"
    for username, event_type, event_value, channel_name, timestamp in rows:
        response += f"- `{timestamp}` | `{username}` | `{event_type}` | `{event_value}` | `#{channel_name}`\n"

    await send_admin_report(ctx, response)


@bot.command()
async def project_help(ctx):
    await ctx.send(
        "**CommunityBot Commands**\n\n"
        "**For users:**\n"
        "`!join` — create/open your private onboarding channel\n"
        "`!profile` — show profile\n"
        "`!recommend` — channel recommendations\n"
        "`!ai_recommend` — AI explanation for recommendations\n"
        "`!teammate_nudge` — teammate suggestions\n"
        "You can also write: `show my profile`, `recommend me a channel`, `find teammates`.\n\n"
        "**For admins:**\n"
        "`!setup_server` — create server channels\n`!fresh_setup CONFIRM` — delete old channels and rebuild clean structure\n"
        "`!event_nudge fps Friday PUBG Event` — event nudge\n"
        "`!channel_nudge fps #fps-discussion` — channel nudge\n"
        "`!community_status` — report to #bot-logs\n"
        "`!evaluation_summary` — evaluation data to #bot-logs\n"
        "`!leader_candidates` — active contributors to #bot-logs\n"
        "`!recent_logs 10` — recent logs to #bot-logs"
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("I did not understand. Use `!project_help`.")
        return

    await ctx.send(f"Error: `{error}`")


if not DISCORD_TOKEN:
    print("ERROR: DISCORD_TOKEN not found. Check your .env file.")
else:
    bot.run(DISCORD_TOKEN)
