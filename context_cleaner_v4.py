import re
import unicodedata
from typing import Dict, Tuple
import emoji


def normalize_emojis(text: str) -> str:
    return emoji.demojize(text, language="en")


def remove_forwards_quotes(text: str) -> str:
    lines = text.splitlines()
    out = []
    skip = False
    markers = (
        "Forwarded message",
        "Begin forwarded message",
        "-----Original Message-----",
        "----- Forwarded Message -----",
        "From:",
        "Sent:",
        "To:",
    )
    for l in lines:
        s = l.strip()
        if skip and not s:
            skip = False
            continue
        if skip:
            continue
        if s.startswith(">"):
            continue
        if re.match(r"^On .+ wrote:\s*$", s):
            skip = True
            continue
        if any(s.startswith(m) for m in markers):
            continue
        if skip and s:
            continue
        out.append(s)
    x = "\n".join(out)
    x = re.sub(r"(?mi)^Begin forwarded message.*$", "", x)
    x = re.sub(r"(?mi)^Forwarded message.*$", "", x)
    x = re.sub(r"(?mi)^-----+\s*(Original|Forwarded)\s*Message\s*-----+$", "", x)
    x = re.sub(r"(?mi)^On .+ wrote:\s*$", "", x)
    x = re.sub(r"(?mi)^>.*$", "", x)
    return re.sub(r"\n+", "\n", x).strip()


def detect_reply_chains(text: str) -> Dict[str, str]:
    t = text.lower()
    m = re.search(r"\b(replying to|replied to)\b[:\s]*([\"']?)(.+?)\2(\.|!|\?|$)", text, re.IGNORECASE)
    if m:
        return {"is_reply": "true", "reply_to": m.group(3).strip()}
    if "re:" in t or "fw:" in t or "fwd:" in t:
        return {"is_reply": "true", "reply_to": "thread"}
    if re.search(r"^On .+ wrote:\s*$", text, re.MULTILINE):
        return {"is_reply": "true", "reply_to": "quoted"}
    return {"is_reply": "false", "reply_to": ""}


def detect_repeated_text(text: str) -> str:
    text = re.sub(r"([!?.])\1{1,}", r"\1", text)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    tokens = text.split()
    if not tokens:
        return text
    dedup = [tokens[0]]
    for tok in tokens[1:]:
        if tok != dedup[-1]:
            dedup.append(tok)
    return " ".join(dedup)


def unify_punctuation(text: str) -> str:
    trans = {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "—": "-",
        "–": "-",
        "…": "...",
    }
    for k, v in trans.items():
        text = text.replace(k, v)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_all(platform: str, text: str) -> Tuple[str, Dict[str, str]]:
    x = remove_forwards_quotes(text)
    x = unify_punctuation(x)
    x = normalize_emojis(x)
    x = detect_repeated_text(x)
    meta = detect_reply_chains(x)
    return x, meta

