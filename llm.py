import json
from openai import OpenAI
from config import MISTRAL_API_KEY, MISTRAL_MODEL, ALLOWED_INTERESTS, ALLOWED_GOALS, ALLOWED_EXPERIENCE

client = OpenAI(
    api_key=MISTRAL_API_KEY,
    base_url="https://api.mistral.ai/v1"
)


def ask_mistral_sync(system_prompt, user_prompt, max_tokens=500):
    if not MISTRAL_API_KEY:
        return "LLM is not connected. MISTRAL_API_KEY is missing."

    response = client.chat.completions.create(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content


def extract_json(text):
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(text[start:end + 1])
    except Exception:
        return None


def fallback_persona(interests_text, goal_text, experience_text, preferences_text):
    full = f"{interests_text} {goal_text} {experience_text} {preferences_text}".lower()

    keyword_map = {
        "fps": ["fps", "pubg", "valorant", "shooter", "shooting", "cs2", "csgo", "cod", "call of duty"],
        "rpg": ["rpg", "roleplay", "role play", "quest", "fantasy"],
        "strategy": ["strategy", "tactic", "tactical", "planning", "chess"],
        "casual": ["casual", "chill", "relax", "relaxed", "fun", "social"],
        "tech": ["tech", "technology", "bot", "python", "coding", "setup"],
        "events": ["event", "events", "tournament", "session", "meetup", "night"]
    }

    interests = []

    for interest, keywords in keyword_map.items():
        if any(keyword in full for keyword in keywords):
            interests.append(interest)

    if "team" in full or "teammate" in full or "squad" in full or "friend" in full:
        goal = "teammates"
    elif "event" in full or "tournament" in full:
        goal = "events"
    elif "help" in full:
        goal = "help"
    elif "talk" in full or "chat" in full or "discussion" in full:
        goal = "discussion"
    else:
        goal = "not provided"

    experience = experience_text if experience_text in ALLOWED_EXPERIENCE else "not provided"

    return {
        "interests": interests,
        "goal": goal,
        "experience": experience,
        "preferences": preferences_text.strip() if preferences_text.strip() else "not provided",
        "raw_interests": interests_text,
        "raw_goal": goal_text,
        "raw_experience": experience_text,
        "raw_preferences": preferences_text
    }


def create_persona_with_llm(interests_text, goal_text, experience_text, preferences_text):
    if not MISTRAL_API_KEY:
        return fallback_persona(interests_text, goal_text, experience_text, preferences_text)

    system_prompt = (
        "You create a structured onboarding profile for a Discord community bot. "
        "Return ONLY valid JSON. Do not invent information. "
        "If something was not provided, write 'not provided'."
    )

    user_prompt = (
        "The user answered onboarding questions.\n\n"
        f"Interests:\n{interests_text}\n\n"
        f"Goal:\n{goal_text}\n\n"
        f"Experience:\n{experience_text}\n\n"
        f"Preferences:\n{preferences_text}\n\n"
        "Return JSON exactly with this structure:\n"
        "{\n"
        '  "interests": [],\n'
        '  "goal": "not provided",\n'
        '  "experience": "not provided",\n'
        '  "preferences": "not provided",\n'
        '  "raw_interests": "",\n'
        '  "raw_goal": "",\n'
        '  "raw_experience": "",\n'
        '  "raw_preferences": ""\n'
        "}\n\n"
        "Allowed interests: fps, rpg, strategy, casual, tech, events.\n"
        "Allowed goals: teammates, events, discussion, help, not provided.\n"
        "Allowed experience: beginner, intermediate, advanced, not provided.\n"
        "Do not add other fields."
    )

    try:
        answer = ask_mistral_sync(system_prompt, user_prompt, 350)
        parsed = extract_json(answer)

        if parsed is None:
            return fallback_persona(interests_text, goal_text, experience_text, preferences_text)

        parsed.setdefault("interests", [])
        parsed.setdefault("goal", "not provided")
        parsed.setdefault("experience", "not provided")
        parsed.setdefault("preferences", "not provided")
        parsed["raw_interests"] = interests_text
        parsed["raw_goal"] = goal_text
        parsed["raw_experience"] = experience_text
        parsed["raw_preferences"] = preferences_text

        parsed["interests"] = [item for item in parsed["interests"] if item in ALLOWED_INTERESTS]

        if parsed["goal"] not in ALLOWED_GOALS:
            parsed["goal"] = "not provided"

        if parsed["experience"] not in ALLOWED_EXPERIENCE:
            parsed["experience"] = "not provided"

        return parsed

    except Exception:
        return fallback_persona(interests_text, goal_text, experience_text, preferences_text)


def community_assistant_answer(question, persona=None):
    persona_context = persona if persona else "No onboarding profile available yet."

    system_prompt = (
        "You are CommunityBot, a Discord community assistant for a gaming community. "
        "You help with onboarding, relevant channels, teammates, events, nudges, "
        "recommendations and community participation. "
        "Keep answers short, friendly and useful. "
        "If the user asks unrelated questions, gently redirect to community support. "
        "Use the user's persona when available."
    )

    user_prompt = f"User persona:\n{persona_context}\n\nUser message:\n{question}"
    return ask_mistral_sync(system_prompt, user_prompt, 500)


def explain_recommendations_with_llm(persona, recommendations_text):
    system_prompt = (
        "You are a friendly Discord onboarding assistant. "
        "Explain channel recommendations briefly. "
        "Only use the profile and channels provided. Do not invent."
    )

    user_prompt = (
        f"User profile:\n{persona}\n\n"
        f"Recommended channels:\n{recommendations_text}\n\n"
        "Explain why these channels are useful. Keep it short."
    )

    return ask_mistral_sync(system_prompt, user_prompt, 350)


def generate_discussion_prompt(channel_name):
    return ask_mistral_sync(
        "Generate one short Discord discussion prompt.",
        f"Generate one short engaging prompt for #{channel_name}.",
        250
    )
