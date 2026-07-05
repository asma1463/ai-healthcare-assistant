PROVIDER_KEYWORDS = {
    "dermatologist": [
        "acne",
        "rash",
        "skin",
        "eczema",
        "psoriasis",
        "pimple",
        "mole",
        "itching",
    ],
    "hospital": [
        "chest pain",
        "shortness of breath",
        "severe pain",
        "stroke",
        "heart attack",
        "emergency",
        "fainting",
        "unconscious",
        "bleeding",
    ],
    "pharmacy": ["medicine", "medication", "prescription", "tablet", "drug"],
    "clinic": ["clinic", "checkup", "follow up", "fever", "cough", "infection"],
    "general physician": [
        "doctor",
        "physician",
        "consult",
        "appointment",
        "symptom",
        "symptoms",
        "since yesterday",
        "for weeks",
        "for months",
    ],
}


def choose_provider_type(question: str, answer: str = ""):
    text = f"{question} {answer}".lower()
    for provider_type, keywords in PROVIDER_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return provider_type
    return None


def recommendation_message(provider_type: str):
    if provider_type == "hospital":
        return (
            "If your symptoms are severe, worsening, or include chest pain, breathing "
            "trouble, fainting, or heavy bleeding, consider urgent medical evaluation."
        )
    if provider_type == "dermatologist":
        return "You may benefit from consulting a dermatologist if symptoms persist or worsen."
    if provider_type == "pharmacy":
        return "A pharmacist may help with medication availability and basic medicine guidance."
    if provider_type == "general physician":
        return "You may benefit from consulting a general physician for an in-person evaluation."
    return "Here are some nearby healthcare providers that may be helpful."
