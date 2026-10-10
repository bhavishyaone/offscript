"""Apply the Phase 3 review to the v2 draft: specific reasons, natural contexts, varied prefixes,
Hinglish casing, near-copy rewording, and new general families that keep a real step.

Reads training/data/v2/router_draft.jsonl + router_metadata.jsonl (unchanged) and writes
training/data/v2/router_v2.jsonl + router_v2_metadata.jsonl.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from new_families import NEW_FAMILIES  # noqa: E402
from reasons import REASONS  # noqa: E402

D = Path("training/data/v2")
with open(D / "router_draft.jsonl", encoding="utf-8") as f:
    rows = [json.loads(line) for line in f]
with open(D / "router_metadata.jsonl", encoding="utf-8") as f:
    meta = {m["id"]: m for m in (json.loads(line) for line in f)}

GENERAL_AI_CTX = [
    "revising for an exam in {city}",
    "my younger cousin asked me this, we're in {city}",
    "came up while chatting with friends in {city}",
    "read about it on the bus in {city}",
    "helping with homework at home in {city}",
    "for a work presentation in {city}",
]
FIELD_AI_CTX = [
    "first time trying this, this weekend in {city}",
    "going with a friend on Sunday in {city}",
    "{city}, trying this for the first time",
    "visiting {city} next week and want to try it",
    "after work one day this week in {city}",
]
SEARCH_FIELD_CTX = [
    "planning a visit this week",
    "going with family if it works out",
    "deciding whether to make the trip",
    "travelling in from another city for this",
    "want to go after work",
]
SEARCH_GENERAL_CTX = [
    "need it for a form I'm filling in",
    "settling a debate with a friend",
    "for a report I'm writing",
    "just curious",
    "need it to plan my week",
]
HUMAN_GENERAL_CTX = [
    "thinking about applying there next year",
    "might move there soon",
    "a friend is considering it",
    "deciding whether it suits me",
    "want an honest picture before deciding",
]
HINGLISH_PREFIXES = [
    "Zara batao,",
    "Ek baat batao,",
    "Mujhe samjhao,",
    "Quick question,",
    "Batao na,",
]
REPHRASE_PREFIXES = [
    "Could you help me with this:",
    "Quick question:",
    "I was wondering:",
    "Can you tell me:",
]

REWORD = {
    # near-copies of golden R11 and R14
    "v2-0691": "What do people who shop here often pick up from this stall?",
    "v2-0811": "Where do students on this campus usually grab lunch between lectures?",
    "v2-1027": "Which way should I head?",  # regression Q171 near-copy (context pair 9)
    "v2-1028": "Which way should I head?",
    "v2-0227": "What's the right way to read a marked trail sign before starting?",
    "v2-0317": "What's an easy way to make a simple sketch of a tree from a bench?",
    "v2-0732": "Is tea stall par pehli baar kaunsi chai try karun?",
}


def pick(pool, index):
    return pool[index % len(pool)]


def hinglish_case(text, english_question):
    """Lowercase the first letter after a prefix unless the first word is a proper noun."""
    first = re.match(r"[A-Za-z][\w-]*", text)
    if first and re.search(rf"(?<!^)\b{re.escape(first.group(0))}\b", english_question):
        return text
    return text[0].lower() + text[1:] if text else text


fam = defaultdict(list)
order = []
for row in rows:
    seed = meta[row["id"]]["seed"]
    if seed not in fam:
        order.append(seed)
    fam[seed].append(row)

out_rows, out_meta = [], []
style_counts = defaultdict(int)  # rotate pools per style, so 5-row families don't repeat one choice
for seed in order:
    family = fam[seed]
    normal = family[0]
    first_hinglish = next(
        (
            r["question"]
            for r in family
            if meta[r["id"]]["style"] == "hinglish" and not r["question"].startswith("Zara batao")
        ),
        None,
    )
    for row in family:
        row = dict(row)
        m = dict(meta[row["id"]])
        style, segment = m["style"], m["segment"]
        style_counts[(style, row["route"], segment)] += 1
        counter = style_counts[(style, row["route"], segment)]
        if isinstance(seed, int):
            row["reason"] = REASONS[seed]
        q = row["question"]
        if style == "hinglish" and q.startswith("Zara batao:") and first_hinglish:
            text = hinglish_case(first_hinglish, normal["question"])
            row["question"] = f"{pick(HINGLISH_PREFIXES, counter)} {text}"
        elif style == "rephrased" and q.startswith("Could you help me answer this:"):
            row["question"] = f"{pick(REPHRASE_PREFIXES, counter)} {q.split(':', 1)[1].strip()}"
        elif style == "contextual":
            city = re.match(r"I'm (?:in|planning to try this in) ([A-Z]\w+)", q)
            if row["route"] == "AI" and city:
                row["question"] = q.split(". ", 1)[1]
                pool = GENERAL_AI_CTX if segment == "general" else FIELD_AI_CTX
                row["context"] = pick(pool, counter).format(city=city.group(1))
            elif row["route"] == "SEARCH":
                row["context"] = pick(
                    SEARCH_GENERAL_CTX if segment == "general" else SEARCH_FIELD_CTX, counter
                )
            elif row["route"] == "HUMAN" and segment == "general":
                row["context"] = pick(HUMAN_GENERAL_CTX, counter)
        if row["id"] in REWORD:
            row["question"] = REWORD[row["id"]]
        if row["id"] == "v2-0735":  # second Hinglish wording of the tea-stall family
            row["question"] = "Batao na, is tea stall par pehli baar kaunsi chai try karun?"
        m["review_status"] = "reviewed_ai_assisted"
        out_rows.append(row)
        out_meta.append(m)

# New general families that keep a real step (decision 2).
styles = ["normal", "hinglish", "short", "contextual", "rephrased"]
next_id = 1031
for offset, family in enumerate(NEW_FAMILIES):
    seed = 203 + offset
    for style, q in zip(styles, family["questions"], strict=True):
        question, context = q if isinstance(q, tuple) else (q, "")
        row = {
            "id": f"v2-{next_id:04d}",
            "question": question,
            "context": context,
            "route": family["route"],
            "reason": family["reason"],
        }
        if family["route"] == "AI":
            row["answer"] = family["answer"]
        else:
            row["search_query"] = family["search_query"]
        row["outdoor_action"] = family["outdoor_action"]
        out_rows.append(row)
        out_meta.append(
            {
                "id": row["id"],
                "seed": seed,
                "topic": family["topic"],
                "segment": "general",
                "style": style,
                "action": "step",
                "review_status": "reviewed_ai_assisted",
            }
        )
        next_id += 1

with open(D / "router_v2.jsonl", "w", encoding="utf-8") as f:
    for row in out_rows:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
with open(D / "router_v2_metadata.jsonl", "w", encoding="utf-8") as f:
    for m in out_meta:
        f.write(json.dumps(m, ensure_ascii=False) + "\n")
print(f"wrote {len(out_rows)} rows and {len(out_meta)} metadata lines")
