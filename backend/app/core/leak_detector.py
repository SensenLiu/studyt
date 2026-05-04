"""Answer-leak detector: regex-based, fast, runs on every tutor turn.

Strategy:
1. Normalize both reference answer and response (strip punctuation, lowercase, unify Chinese numerals).
2. Split reference into atomic value tokens (e.g. "x=2,y=3" → ["x=2","y=3"] → numbers ["2","3"]).
3. A leak is declared if EVERY non-trivial numeric/symbolic token from the reference appears in the response as a standalone token (word-boundary check).

This is intentionally conservative: false positives (over-flagging) are
acceptable for M0 — we'd rather refuse a legit response than leak. We can
loosen later if too noisy.
"""
from __future__ import annotations
import re
import unicodedata

_CN_NUMS = {"零": "0", "一": "1", "二": "2", "三": "3", "四": "4",
            "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    # convert Chinese digits
    for cn, ar in _CN_NUMS.items():
        s = s.replace(cn, ar)
    # remove whitespace and common punctuation (including ASCII period)
    s = re.sub(r"[\s.,，。．、:：;；!！?？]+", "", s)
    return s


_TOKEN_RE = re.compile(r"[a-z]?=?-?\d+(?:\.\d+)?")


def _atomic_tokens(reference: str) -> list[str]:
    norm = normalize(reference)
    tokens = _TOKEN_RE.findall(norm)
    if not tokens:
        # fallback: take normalized whole string as single token
        return [norm] if norm else []
    return tokens


def detect_answer_leak(response_text: str, reference_answer: str) -> bool:
    tokens = _atomic_tokens(reference_answer)
    if not tokens:
        return False
    norm_resp = normalize(response_text)
    # require word-ish boundaries for plain numbers to avoid "12" matching "120"
    for tok in tokens:
        # build a regex for boundary: digit-only tokens need \D-or-edge boundary
        if re.fullmatch(r"\d+(?:\.\d+)?", tok):
            pat = rf"(?<!\d){re.escape(tok)}(?!\d)"
            if not re.search(pat, norm_resp):
                return False
        else:
            # For "var=number" tokens (e.g. "x=3"), also accept just the numeric
            # part appearing standalone — handles "x 等于 三" → norm "x等于3"
            m = re.fullmatch(r"[a-z]+=(-?\d+(?:\.\d+)?)", tok)
            if m:
                num = m.group(1)
                exact_pat = rf"(?<!\d){re.escape(num)}(?!\d)"
                if re.search(re.escape(tok), norm_resp) or re.search(exact_pat, norm_resp):
                    continue
                return False
            pat = re.escape(tok)
            if not re.search(pat, norm_resp):
                return False
    return True
