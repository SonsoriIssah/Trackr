"""
task_breakdown.py
Rule-based goal decomposition module for Trackr.

Usage:
    from task_breakdown import breakdown_goal, breakdown_goal_json

    subtasks = breakdown_goal("Build my portfolio website")
    # => ["Define project requirements...", "Set up environment...", ...]

    json_str = breakdown_goal_json("Study for my final exams")
    # => JSON string of the subtask list
"""

import re
import json

# ---------------------------------------------------------------------------
# Category definitions: keywords → subtask templates
# ---------------------------------------------------------------------------

_CATEGORIES = {
    "software": {
        "keywords": [
            "build", "create", "develop", "website", "web", "app", "application",
            "portfolio", "code", "program", "software", "api", "database", "deploy",
            "backend", "frontend", "flutter", "react", "python", "django", "flask",
            "javascript", "typescript", "android", "ios", "mobile", "server",
            "debug", "fix", "refactor", "script", "automate", "bot", "game",
            "ui", "ux", "interface", "feature", "github", "repository", "tool",
        ],
        "subtasks": [
            "Define the project requirements and scope",
            "Design the architecture and data models",
            "Set up the development environment and project structure",
            "Build the core features and functionality",
            "Style the user interface and improve the user experience",
            "Write tests, find and fix bugs",
            "Deploy the application and write documentation",
        ],
    },
    "studying": {
        "keywords": [
            "study", "learn", "read", "understand", "prepare", "exam", "test",
            "course", "lecture", "revise", "master", "tutorial", "assignment",
            "thesis", "research", "paper", "subject", "math", "science", "history",
            "quiz", "grade", "university", "school", "college", "homework",
            "notes", "textbook", "chapter", "module", "certificate", "certification",
            "class", "lesson", "curriculum", "degree", "language",
        ],
        "subtasks": [
            "Gather all study materials and resources",
            "Create a structured study schedule with daily targets",
            "Take detailed notes on key concepts and definitions",
            "Practice with past questions, exercises, or problem sets",
            "Review and reinforce the topics where you feel weakest",
            "Test yourself with mock assessments or flashcards",
            "Summarize everything and consolidate your understanding",
        ],
    },
    "fitness": {
        "keywords": [
            "workout", "exercise", "gym", "run", "running", "lose weight",
            "gain muscle", "fitness", "diet", "health", "train", "marathon",
            "yoga", "swim", "cycling", "sport", "athletic", "strength", "cardio",
            "calories", "nutrition", "weight", "muscle", "fat", "lean",
            "jog", "walk", "steps", "active", "healthy", "routine", "body",
            "stretch", "lift", "rep", "squat", "push", "endurance",
        ],
        "subtasks": [
            "Set specific, measurable fitness goals with a target date",
            "Create a weekly workout plan and rest schedule",
            "Prepare your equipment, gear, or workout space",
            "Include a warm-up routine before every session",
            "Execute the main workout consistently on planned days",
            "Track your progress (reps, distance, weight) each session",
            "Review your nutrition, hydration, and recovery habits weekly",
        ],
    },
    "business": {
        "keywords": [
            "business", "startup", "launch", "market", "sell", "product", "customer",
            "brand", "revenue", "pitch", "monetize", "invest", "entrepreneur",
            "company", "service", "client", "profit", "sales", "marketing",
            "ecommerce", "store", "shop", "freelance", "agency", "consulting",
            "partnership", "fund", "investor", "mvp", "scale", "growth", "plan",
            "hire", "team", "strategy", "competitor", "niche", "audience",
        ],
        "subtasks": [
            "Research your target market, audience, and competitors",
            "Define your value proposition and unique selling point",
            "Build a minimum viable product (MVP) or prototype",
            "Set up your business presence (website, social media, branding)",
            "Identify and reach out to your first potential customers",
            "Define your pricing strategy and revenue model",
            "Track key metrics and iterate based on real feedback",
        ],
    },
    "personal": {
        "keywords": [
            "organize", "clean", "plan", "habit", "routine", "journal", "meditate",
            "meditation", "improve", "personal", "life", "home", "travel", "move",
            "family", "relationship", "social", "skill", "cook", "sleep", "stress",
            "anxiety", "mindset", "confidence", "communication", "network",
            "friend", "hobby", "creative", "art", "music", "write", "read more",
            "declutter", "budget", "save", "money", "finance", "self", "mental",
        ],
        "subtasks": [
            "Write down your goal clearly and define what success looks like",
            "Break the goal into smaller weekly milestones",
            "Identify the resources, tools, or support you need",
            "Build a daily habit or routine that moves you toward the goal",
            "Take your first concrete action step today",
            "Review your progress at the end of each week",
            "Stay accountable — share your goal with someone you trust",
        ],
    },
}

_GENERAL_SUBTASKS = [
    "Write down your goal clearly and define what success looks like",
    "Research what you need to know or have to achieve this goal",
    "Break the goal into smaller, manageable milestones",
    "Create a realistic timeline with deadlines for each milestone",
    "Take the first concrete action step immediately",
    "Review your progress regularly and adjust the plan as needed",
    "Celebrate small wins along the way to stay motivated",
]

# Leading verbs that strongly imply a specific category (boost that category by +2)
_INTENT_VERB_BOOSTS = {
    "studying":  {"learn", "study", "revise", "understand", "memorize", "research"},
    "fitness":   {"train", "exercise", "workout", "run", "jog", "swim", "cycle"},
    "business":  {"sell", "pitch", "monetize", "market"},
    "personal":  {"meditate", "journal", "declutter", "organize", "improve"},
    "software":  {"code", "program", "deploy", "debug", "refactor", "automate", "develop"},
}

# Verbs commonly found at the start of a goal phrase (used for subject extraction)
_LEADING_VERBS = re.compile(
    r"^(?:build|create|develop|make|design|launch|start|finish|complete|write"
    r"|learn|study|prepare\s+for|get|become|improve|organize|run|train\s+for"
    r"|set\s+up|put\s+together|work\s+on|grow|plan)\s+(?:a\s+|an\s+|my\s+|the\s+)?",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> set:
    return set(re.findall(r"\b\w+\b", text.lower()))


def _detect_category(goal: str) -> str:
    tokens = _tokenize(goal)
    goal_lower = goal.lower()
    scores: dict[str, int] = {}

    for category, data in _CATEGORIES.items():
        score = 0
        for kw in data["keywords"]:
            if " " in kw:
                if kw in goal_lower:
                    score += 2
            elif kw in tokens:
                score += 1
        scores[category] = score

    # Boost categories whose intent verbs appear in the goal
    for category, intent_verbs in _INTENT_VERB_BOOSTS.items():
        if tokens & intent_verbs:
            scores[category] = scores.get(category, 0) + 2

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def _extract_subject(goal: str) -> str:
    stripped = _LEADING_VERBS.sub("", goal.strip())
    # Remove lingering prepositions left by verbs like "study for"
    stripped = re.sub(r"^(?:for|to|on|about)\s+(?:my\s+|the\s+|a\s+|an\s+)?", "", stripped, flags=re.IGNORECASE)
    return stripped if stripped != goal.strip() else goal.strip()


def _subtask_count(goal: str) -> int:
    word_count = len(goal.split())
    if word_count <= 3:
        return 4
    if word_count <= 5:
        return 5
    if word_count <= 8:
        return 6
    return 7


def _personalize(subtasks: list, subject: str) -> list:
    if not subject:
        return subtasks

    result = []
    s = subject.capitalize()
    for i, task in enumerate(subtasks):
        if i == 0:
            task = (
                task
                .replace("the project requirements", f"the requirements for {s}")
                .replace("your goal clearly", f'your goal ("{s}") clearly')
                .replace("all study materials", f"study materials for {s}")
                .replace("specific, measurable fitness goals", f"specific goals for {s}")
                .replace("your target market", f"the market for {s}")
            )
        result.append(task)
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def breakdown_goal(goal: str) -> list:
    """
    Break a high-level goal string into 3-7 actionable subtasks.

    Args:
        goal: Plain-text goal description, e.g. "Build my portfolio website"

    Returns:
        List of subtask strings (3-7 items).
    """
    if not goal or not goal.strip():
        return ["Define your goal clearly before breaking it down into steps"]

    category = _detect_category(goal)
    subject = _extract_subject(goal)
    count = _subtask_count(goal)

    template = (
        _GENERAL_SUBTASKS if category == "general"
        else _CATEGORIES[category]["subtasks"]
    )

    subtasks = _personalize(template[:count], subject)
    return subtasks


def breakdown_goal_json(goal: str) -> str:
    """Same as breakdown_goal but returns a JSON string."""
    return json.dumps(breakdown_goal(goal), indent=2)


# ---------------------------------------------------------------------------
# Quick smoke-test when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _demos = [
        "Build my portfolio website",
        "Study for my final university exams",
        "Train for a half marathon",
        "Launch my e-commerce startup",
        "Organize my daily life and build better habits",
        "Learn Spanish",
        "Fix the login bug in my app",
    ]
    for g in _demos:
        print(f"\nGoal : {g}")
        print(breakdown_goal_json(g))
