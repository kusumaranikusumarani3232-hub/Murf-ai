import json
from pathlib import Path


DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "cefr-sp.json"


def _load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_learning_exercise(level: str, topic: str = "") -> str:
    """
    Get an English practice sentence from the public CEFR dataset.

    The dataset provides English sentences labeled from A1 to C2.
    """

    level = level.strip().upper()
    topic = topic.strip().lower()

    level_map = {
        "BEGINNER": "A1",
        "ELEMENTARY": "A2",
        "INTERMEDIATE": "B1",
        "UPPER-INTERMEDIATE": "B2",
        "ADVANCED": "C1",
        "PROFICIENT": "C2",
    }

    cefr_level = level_map.get(level, level)

    if cefr_level not in {"A1", "A2", "B1", "B2", "C1", "C2"}:
        return (
            "I couldn't find a matching CEFR level. "
            "Please try beginner, intermediate, or advanced."
        )

    try:
        data = _load_dataset()
    except Exception:
        return (
            "I'm sorry, I couldn't access the English learning dataset "
            "right now. Please try again later."
        )

    matches = [
        item
        for item in data
        if item.get("lang") == "en"
        and item.get("cefr_level") == cefr_level
        and item.get("text")
    ]

    if not matches:
        return "I couldn't find an exercise for that level right now."

    # If a topic is supplied, prefer sentences containing the topic.
    if topic:
        topic_matches = [
            item
            for item in matches
            if topic in item.get("text", "").lower()
        ]

        if topic_matches:
            matches = topic_matches

    # Deterministic selection keeps the demo predictable.
    selected = matches[0]

    return (
        f"Here is a {cefr_level} English practice sentence: "
        f"{selected['text']}"
    )