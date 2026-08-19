"""
Turns a block of text into a list of "fill in the blank" prompts for the
Concept Map active-recall game (Module 3, Lamia) -- entirely local,
zero AI calls, same "one function everything else calls" shape as
utils/dictionary.py and utils/ocr.py.

WHY THIS ISN'T A TREE DIAGRAM: the original design brief for this feature
described a branching tree with semantically-labeled categories (e.g.
grouping "First law" and "Second law" under a branch called "Laws"). That
kind of grouping requires actually understanding what the concepts mean,
which NLTK's part-of-speech tagging genuinely cannot do -- it can find
"a first law" is a noun phrase, but has no way to know it belongs under
a category called "Laws" rather than, say, "Rules" or nothing at all.
Getting that would need an AI call, which defeats the "no AI call, no
API cost" point of building this with NLTK/regex in the first place. So
instead: every extracted concept becomes a blank in the ORIGINAL sentence
it came from -- something NLTK actually can find reliably -- and the
game is "read the sentence, drag in the missing word" rather than
"reconstruct a hierarchy the extractor never actually inferred".

TWO EXTRACTION MODES:
  - extract_text_blanks(): general prose (biology, black holes, linked
    lists, ...). Sentence-tokenizes, POS-tags, and chunks noun phrases
    with a regex grammar -- each unique noun phrase becomes one blank in
    the sentence it was found in.
  - extract_formula_blanks(): math/formula text. No NLTK involved at all
    here -- just regex, per the original brief -- isolates the symbol on
    the left of each "=" and blanks that one symbol out of the equation.

MOCK / BASIC-MODE FALLBACK: nltk's sentence/POS models ("punkt",
"averaged_perceptron_tagger") have to be downloaded separately from
`pip install nltk`, same situation as the WordNet corpus in
utils/dictionary.py. If they're missing, extract_text_blanks() falls
back to a cruder, NLTK-free heuristic (longest word per sentence) rather
than failing outright -- clearly flagged via the returned `is_basic_mode`
flag so the frontend can show a "basic extraction" notice instead of
silently producing lower-quality blanks with no explanation.
"""

import re

_nltk_checked = False
_nltk_available = False


def _ensure_nltk() -> bool:
    global _nltk_checked, _nltk_available
    if _nltk_checked:
        return _nltk_available
    _nltk_checked = True
    try:
        import nltk
        nltk.sent_tokenize("Test sentence.")               # needs "punkt"
        nltk.pos_tag(nltk.word_tokenize("a test sentence"))  # needs "averaged_perceptron_tagger"
        _nltk_available = True
    except Exception:  # noqa: BLE001 -- covers ImportError and any LookupError variant
        _nltk_available = False
    return _nltk_available


def _clean_source_text(text: str) -> str:
    """Strips Markdown/LaTeX syntax that would otherwise confuse sentence
    tokenization (headings, bullets, bold markers, inline math)."""
    text = re.sub(r"\$\$?(.+?)\$\$?", r"\1", text, flags=re.DOTALL)  # unwrap $...$ / $$...$$
    text = re.sub(r"[#*_`]", "", text)
    text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.MULTILINE)
    return text.strip()


# --------------------------------------------------------------------------
# General text -> noun-phrase blanks
# --------------------------------------------------------------------------

_MIN_ANSWER_LEN = 3   # skip trivially short/uninteresting noun phrases like "it", "a way"
_STOPWORDS = {"the", "a", "an", "this", "that", "these", "those", "it", "its"}


def _nltk_noun_phrases(sentence: str) -> list[str]:
    import nltk

    tokens = nltk.word_tokenize(sentence)
    tagged = nltk.pos_tag(tokens)
    # A noun phrase is an optional determiner/adjectives followed by one
    # or more nouns -- e.g. "a black hole", "the second law" ->
    # ("black hole", "second law").
    grammar = "NP: {<DT>?<JJ.*>*<NN.*>+}"
    parser = nltk.RegexpParser(grammar)
    tree = parser.parse(tagged)

    phrases = []
    for subtree in tree.subtrees(filter=lambda t: t.label() == "NP"):
        words = [w for w, _tag in subtree.leaves()]
        if words and words[0].lower() in _STOPWORDS:
            words = words[1:]
        phrase = " ".join(words).strip()
        if len(phrase) >= _MIN_ANSWER_LEN:
            phrases.append(phrase)
    return phrases


def _basic_sentence_answer(sentence: str) -> str | None:
    """NLTK-free fallback: just the longest word in the sentence, which
    tends to land on a real term more often than picking at random --
    crude, but the whole point of a fallback is "still works", not
    "works as well"."""
    words = re.findall(r"[A-Za-z][A-Za-z\-]{4,}", sentence)
    if not words:
        return None
    return max(words, key=len)


def extract_text_blanks(text: str, *, max_items: int = 10) -> tuple[list[dict], bool]:
    """Returns (items, is_basic_mode). Each item is
    {"id": str, "template": str, "answer": str} where `template` contains
    the sentence with the answer replaced by "___"."""
    cleaned = _clean_source_text(text)
    use_nltk = _ensure_nltk()

    if use_nltk:
        import nltk
        sentences = nltk.sent_tokenize(cleaned)
    else:
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)

    items: list[dict] = []
    seen_answers: set[str] = set()

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 15:  # too short to make a meaningful blank
            continue

        candidates = _nltk_noun_phrases(sentence) if use_nltk else (
            [a] if (a := _basic_sentence_answer(sentence)) else []
        )
        if not candidates:
            continue

        # Prefer the longest candidate phrase in the sentence -- usually
        # the most specific/interesting term, and least likely to also
        # appear as a sub-phrase of something else already picked.
        answer = max(candidates, key=len)
        key = answer.lower()
        if key in seen_answers:
            continue

        # Blank out only the first occurrence, case-insensitively.
        pattern = re.compile(re.escape(answer), re.IGNORECASE)
        template, count = pattern.subn("___", sentence, count=1)
        if count == 0:
            continue

        seen_answers.add(key)
        items.append({"id": f"n{len(items) + 1}", "template": template, "answer": answer})

        if len(items) >= max_items:
            break

    return items, not use_nltk


# --------------------------------------------------------------------------
# Math formulas -> variable blanks (pure regex, no NLTK -- per the brief)
# --------------------------------------------------------------------------

# A "variable" is a short identifier on the left of an "=" -- e.g. ΔU, PV,
# S, H -- deliberately excludes plain numbers so we never try to blank
# out a numeric constant.
_EQUATION_RE = re.compile(
    r"(?P<lhs>[A-Za-zΔαβγπΩθλμσ][A-Za-z0-9_ΔαβγπΩθλμσ]{0,6})\s*=\s*(?P<rhs>[^\n,.;]{1,60})"
)


def extract_formula_blanks(text: str, *, max_items: int = 10) -> tuple[list[dict], bool]:
    """Returns (items, is_basic_mode) -- is_basic_mode is always False
    here since this mode never depends on NLTK at all, only regex."""
    cleaned = _clean_source_text(text)
    items: list[dict] = []
    seen: set[str] = set()

    for match in _EQUATION_RE.finditer(cleaned):
        lhs = match.group("lhs").strip()
        rhs = match.group("rhs").strip()
        formula = f"{lhs} = {rhs}"
        key = formula.lower()
        if key in seen or not rhs:
            continue
        seen.add(key)

        template = f"___ = {rhs}"
        items.append({"id": f"n{len(items) + 1}", "template": template, "answer": lhs})

        if len(items) >= max_items:
            break

    return items, False
