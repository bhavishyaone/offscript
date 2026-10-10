"""Rule-based safety and guard checks that run BEFORE the model (AGENTS.md B3 step 2).

These are the ONLY place rules are allowed. A hit returns a guard response
and the model is never called. The model is never trained on safety questions.
"""

import re

from offscript_contract.route_dto import GuardResponse
from offscript_contract.router import RouterInput

# --- Keyword lists ---------------------------------------------------------------

_EMERGENCY_KEYWORDS = [
    "suicide",
    "suicidal",
    "kill myself",
    "self-harm",
    "hurting myself",
    "hurt myself",
    "harm myself",
    "end my life",
    "end my own life",
    "end his life",
    "end her life",
    "end their life",
    "end it all",
    "want to die",
    "wanna die",
    "take my life",
    "take my own life",
    "slit my wrist",
    "slit my wrists",
    "hanging myself",
    "overdose",
    "fainted",
    "unconscious",
    "emergency",
    "call 911",
    "call 999",
    "call 112",
    "ambulance",
]

_MEDICAL_KEYWORDS = [
    "medicine",
    "medication",
    "prescription",
    "drug dosage",
    "doctor",
    "diagnosis",
    "symptom",
    "treatment",
    "therapy",
    "medical advice",
]

_LEGAL_KEYWORDS = [
    "lawyer",
    "legal advice",
    "sue",
    "lawsuit",
    "arrest",
    "court case",
    "bail",
]

_DANGEROUS_ROUTE_KEYWORDS = [
    "dark shortcut",
    "unsafe route",
    "abandoned",
    "trespass",
    "break in",
    "sneak in",
    "climb the fence",
    "hop the fence",
    "hop fence",
    "restricted area",
    "construction site",
    "locked gate",
]

_INTRUSIVE_KEYWORDS = [
    "follow them",
    "follow her",
    "follow him",
    "follow someone",
    "stalk",
    "harass",
    "woman sitting alone",
    "man sitting alone",
    "person sitting alone",
    "why she is alone",
    "why he is alone",
    "why they are alone",
    "record without",
    "film without",
    "photograph without",
    "take a picture without",
    "without consent",
    "without permission",
    "secretly record",
    "secretly photograph",
    "stranger home",
    "private property",
]


def _compile_keywords(keywords: list[str]) -> re.Pattern:
    """Compile keywords with word boundaries to avoid false positives (e.g. 'issue'/'sue')."""
    return re.compile(
        r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")\b",
        re.IGNORECASE,
    )


# Compiled patterns with word boundaries
_EMERGENCY_PATTERN = _compile_keywords(_EMERGENCY_KEYWORDS)
_MEDICAL_PATTERN = _compile_keywords(_MEDICAL_KEYWORDS)
_LEGAL_PATTERN = _compile_keywords(_LEGAL_KEYWORDS)
_DANGEROUS_PATTERN = _compile_keywords(_DANGEROUS_ROUTE_KEYWORDS)
_INTRUSIVE_PATTERN = _compile_keywords(_INTRUSIVE_KEYWORDS)


# --- Public API ------------------------------------------------------------------


def check_safety(
    router_input: RouterInput,
    request_id: str,
    latency_ms: int,
) -> GuardResponse | None:
    """Return a guard response if safety rules trigger, else None.

    Checks are ordered by severity: emergency first, then medical/legal,
    then dangerous routes, then intrusive/targeting requests.
    """
    combined = f"{router_input.question} {router_input.context}"

    # Emergency / immediate safety
    if _EMERGENCY_PATTERN.search(combined):
        return GuardResponse(
            fit="safety_guidance",
            reason="Emergency or immediate safety concern detected.",
            message=(
                "If you or someone nearby is in immediate danger, "
                "please call your local emergency number (911 / 999 / 112). "
                "Offscript cannot provide emergency assistance."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    # Medical / mental-health
    if _MEDICAL_PATTERN.search(combined):
        return GuardResponse(
            fit="safety_guidance",
            reason="Medical or health question requires professional guidance.",
            message=(
                "Please consult a qualified healthcare professional for "
                "medical advice. Offscript is not a substitute for "
                "professional medical guidance."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    # Legal
    if _LEGAL_PATTERN.search(combined):
        return GuardResponse(
            fit="safety_guidance",
            reason="Legal question requires professional counsel.",
            message=(
                "For legal questions, please consult a qualified legal "
                "professional. Offscript cannot provide legal advice."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    # Dangerous routes / trespass
    if _DANGEROUS_PATTERN.search(combined):
        return GuardResponse(
            fit="safety_guidance",
            reason="Potentially unsafe route or location access.",
            message=(
                "This route or location may not be safe. Please choose a "
                "well-lit, public path and never enter restricted areas "
                "without permission."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    # Intrusive / harassing / targeting
    if _INTRUSIVE_PATTERN.search(combined):
        return GuardResponse(
            fit="refusal",
            reason="Request involves intrusive or targeting behaviour.",
            message=(
                "Offscript cannot help with requests that involve following, "
                "harassing, or intruding on other people. Everyone deserves "
                "to feel safe in public spaces."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    return None
