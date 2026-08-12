"""
Local word-lookup, following the exact wrapping pattern as utils/ocr.py
and utils/youtube.py: one function everything else calls, so the actual
lookup engine can be swapped later without touching any caller.

WHY WORDNET (nltk): it's a free, offline lexical database -- once the
corpus is downloaded once (`python -m nltk.downloader wordnet`), every
lookup is a local, in-memory query. No network call, no API key, no rate
limit -- same "zero external API" spirit as the local Tesseract OCR setup
in utils/ocr.py.

WHY A MOCK FALLBACK: the WordNet corpus (~10MB) has to be downloaded
separately from `pip install nltk`, same situation as the tesseract-ocr
binary in utils/ocr.py. Not every teammate will have run the download
step while building other parts of the app, so a missing corpus returns
clearly-labeled placeholder text instead of crashing every lookup.
"""

_wordnet_checked = False
_wordnet_available = False


def _ensure_wordnet() -> bool:
    """
    Import nltk's wordnet corpus once per process, remembering whether it
    actually loaded so later calls don't retry an expensive import/disk
    check on every single request.
    """
    global _wordnet_checked, _wordnet_available
    if _wordnet_checked:
        return _wordnet_available

    _wordnet_checked = True
    try:
        from nltk.corpus import wordnet  # noqa: F401
        wordnet.synsets("test")  # touches the corpus; raises if not downloaded
        _wordnet_available = True
    except Exception:  # noqa: BLE001 -- covers ImportError and LookupError alike
        _wordnet_available = False
    return _wordnet_available


def lookup_word(word: str, topic: str | None = None) -> dict:
    """
    Look up one word using NLTK WordNet completely offline (zero external API calls).
    If a topic is provided, ranks WordNet synsets by keyword relevance to the topic.
    """
    word = word.strip().lower()

    if not word:
        return {
            "word": word,
            "definition": "Nothing to look up.",
            "part_of_speech": None,
            "synonyms": [],
        }

    if not _ensure_wordnet():
        return {
            "word": word,
            "definition": (
                f"WordNet corpus not downloaded on this machine. "
                "Run `python -m nltk.downloader wordnet` once to enable offline definitions."
            ),
            "part_of_speech": None,
            "synonyms": [],
        }

    try:
        from nltk.corpus import wordnet

        synsets = wordnet.synsets(word)
        if not synsets:
            return {
                "word": word,
                "definition": f"No definition found for '{word}'.",
                "part_of_speech": None,
                "synonyms": [],
            }

        best = synsets[0]

        # Domain ranking using local topic keywords (purely offline)
        if topic and len(synsets) > 1:
            topic_lower = topic.lower()
            topic_words = set(topic_lower.replace("-", " ").split())

            best_score = -1
            for syn in synsets:
                defn = syn.definition().lower()
                score = 0
                for tw in topic_words:
                    if len(tw) > 2 and tw in defn:
                        score += 2
                # Additional domain boosting for common computer/tech/science terms
                if any(w in topic_lower for w in ["computer", "program", "software", "oop", "coding", "python", "tech"]):
                    if any(w in defn for w in ["computer", "computing", "program", "software", "system", "data", "code", "network", "variable"]):
                        score += 5

                if score > best_score:
                    best_score = score
                    best = syn

        pos_map = {"n": "noun", "v": "verb", "a": "adjective", "s": "adjective", "r": "adverb"}
        synonyms = sorted({
            lemma.name().replace("_", " ")
            for syn in synsets[:3]
            for lemma in syn.lemmas()
            if lemma.name().replace("_", " ") != word
        })[:4]

        return {
            "word": word,
            "definition": best.definition(),
            "part_of_speech": pos_map.get(best.pos()),
            "synonyms": synonyms,
        }
    except Exception as exc:
        print(f"WordNet lookup error: {exc}")
        return {
            "word": word,
            "definition": f"Definition for '{word}' unavailable.",
            "part_of_speech": None,
            "synonyms": [],
        }
