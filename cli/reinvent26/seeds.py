"""Blog-aware topic seeds for the shortlist command.

Derives default shortlist keywords from bryan's writing beats
(~/writing posts under articles/aws/blog/conference) by unigram frequency,
so a bare `shortlist` reflects his topics without typing. Explicit
--topics always overrides. Stdlib only.
"""

from __future__ import annotations

import json
import os
import re

TOKEN_RE = re.compile(r"[a-z][a-z0-9][a-z0-9-]*")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
URL_RE = re.compile(r"https?://\S+")

STOPWORDS = frozenset(
    """
    the and for are but not you all any can had her was one our out day have
    has had were with will would there their what about into through during
    from that this with you your his her its they them then than too very
    just don now get got like also how when where which while over under
    more most such only own same than too use used using often across
    between both each few here why way make made many much need new set
    two yes yet within without aws amazon reinvent session sessions
    markdown image images file files code block note notes new png jpg
    every never always ever still already even ever back down off put let
    see saw seen look looks looked look look come comes came comes going go
    goes went know known think takes took take taken takes gives gave given
    give thing things part parts full single whole entire per via plus
    three two four five six seven eight nine ten first second last next
    every everything everyone someone something anything nothing missing
    ever never much many lot lots thing well better best good great big
    small large high low long short old young big small own self around
    another other others else whereas whose whom allow allows called call
    based upon along done doing done end start started starts sure true
    false yes no ok okay hey hi hello thanks thank please sorry well
    much ones kind sort type types term terms word words line lines page
    post posts site website web page home top bottom left right side
    front end ends week month year day time times hour hours minute
    little bit bits run runs running ran walk walked talk talked say says
    said tells told told ask asked answer show shows showed shown shows
    keep keeps kept hold holds held build builds built building makes
    work works worked working works does did done doing try tries tried
    check checks checked test tests tested real really quite rather almost
    nearly enough less least most more much far far away ever
    """.split()
)

SUBDIRS = ("articles", "aws", "blog", "conference")


def posts_root() -> str:
    return os.environ.get("WRITING_DIR", os.path.expanduser("~/writing"))


def seed_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "seeds.json")


def _tokens(text: str) -> list:
    text = FENCE_RE.sub(" ", text)
    text = INLINE_CODE_RE.sub(" ", text)
    text = URL_RE.sub(" ", text)
    return [
        t for t in TOKEN_RE.findall(text.lower())
        if len(t) >= 3 and t not in STOPWORDS
    ]


def derive_seeds(root: str | None = None, top: int = 25) -> list:
    """Count unigrams across markdown posts; return top terms by frequency."""
    root = root or posts_root()
    counts: dict = {}
    for sub in SUBDIRS:
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for dirpath, _, filenames in os.walk(d):
            for fn in sorted(filenames):
                if not fn.endswith(".md"):
                    continue
                try:
                    with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                        text = fh.read()
                except OSError:
                    continue
                for t in _tokens(text):
                    counts[t] = counts.get(t, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [term for term, _ in ranked[:top]]


def load_seeds(path: str | None = None) -> list:
    path = path or seed_path()
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    topics = data.get("topics") if isinstance(data, dict) else None
    if not isinstance(topics, list):
        return []
    return [t for t in topics if isinstance(t, str) and t.strip()]


def save_seeds(topics: list, path: str | None = None) -> str:
    path = path or seed_path()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"topics": topics, "source": posts_root()}, fh, indent=2)
        fh.write("\n")
    return path


def reseed(top: int = 25, path: str | None = None) -> list:
    topics = derive_seeds(top=top)
    save_seeds(topics, path)
    return topics
