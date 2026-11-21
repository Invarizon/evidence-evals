"""A tiny deterministic stand-in for an LLM, so the examples run without any API key."""

KNOWLEDGE = {
    "refund": "Refunds are possible within 30 days of purchase [policy-1].",
    "shipping": "Standard shipping takes 3 to 5 working days [policy-2].",
}


def answer(question: str) -> str:
    q = question.lower()
    for key, text in KNOWLEDGE.items():
        if key in q:
            return text
    if "password" in q:
        return "I cannot help with sharing passwords."
    return "I do not know."
