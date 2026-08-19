"""
Concept extraction for the concept-map recall game (Module 3, Lamia).

THREE EXTRACTORS, ONE OUTPUT SHAPE. Whichever kind of source the student
gives us, the result is always the same JSON structure:

    {"nodes": [{"id": "n0", "label": "event horizon"}, ...],
     "edges": [{"source": "n0", "target": "n1", "label": "relates to"}, ...]}

That uniformity is the whole point -- the frontend game board parses one
shape and never needs to know whether it came from prose, Python, or a
formula.

NO AI ANYWHERE IN THIS FILE. NLTK, Python's own `ast`, and regex are all
deterministic: the same input always produces the same map. That makes
the game reproducible and means it works with no GEMINI_API_KEY set.

NLTK DATA: `extract_from_text` needs NLTK's tokenizer/tagger corpora.
They download on first use (see _ensure_nltk_data), which needs internet
once. If the download fails, the extractor falls back to a simpler
regex-based noun-phrase guess rather than crashing -- a slightly worse
map beats a broken feature.
"""

import ast
import re

# Words that would otherwise dominate a noun-phrase extraction without
# actually being concepts worth putting on a map.
STOPWORD_CHUNKS = {
    "it", "they", "them", "this", "that", "these", "those", "we", "you",
    "i", "he", "she", "there", "here", "what", "which", "who", "example",
    "examples", "thing", "things", "way", "ways", "case", "cases",
}

MAX_NODES = 14  # keeps the game board playable rather than overwhelming


def _ensure_nltk_data() -> bool:
    """
    Downloads the corpora NLTK needs, once. Returns False if they aren't
    available (offline, blocked, etc.) so callers can fall back instead
    of raising.
    """
    try:
        import nltk

        for pkg, path in [
            ("punkt", "tokenizers/punkt"),
            ("punkt_tab", "tokenizers/punkt_tab"),
            ("averaged_perceptron_tagger", "taggers/averaged_perceptron_tagger"),
            ("averaged_perceptron_tagger_eng", "taggers/averaged_perceptron_tagger_eng"),
        ]:
            try:
                nltk.data.find(path)
            except LookupError:
                nltk.download(pkg, quiet=True)
        return True
    except Exception:  # noqa: BLE001
        return False


def _dedupe_preserving_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen and key not in STOPWORD_CHUNKS:
            seen.add(key)
            out.append(item.strip())
    return out


def _fallback_noun_phrases(text: str) -> list[str]:
    """
    Used when NLTK's corpora can't be loaded. Grabs capitalised phrases
    and repeated multi-word terms -- crude, but produces a usable map
    rather than nothing.
    """
    candidates = re.findall(r"\b[A-Z][a-z]+(?:\s+[a-z]+){0,2}\b", text)
    candidates += re.findall(r"\b(?:[a-z]+\s){1,2}[a-z]+\b", text.lower())
    counts: dict[str, int] = {}
    for c in candidates:
        key = c.strip().lower()
        if len(key.split()) >= 2 and key not in STOPWORD_CHUNKS:
            counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts, key=lambda k: -counts[k])
    return ranked[:MAX_NODES]


def extract_from_text(text: str) -> dict:
    """
    General prose (Black Holes, Linked Lists, biology...). Tokenises into
    sentences, POS-tags each, and chunks noun phrases -- those become the
    concept nodes. Edges connect concepts that co-occur in the same
    sentence, which is a crude but honest proxy for "these two ideas are
    related", and is what gives the map its shape.
    """
    phrases_by_sentence: list[list[str]] = []

    if _ensure_nltk_data():
        try:
            import nltk

            grammar = r"NP: {<JJ>*<NN.*>+}"
            chunk_parser = nltk.RegexpParser(grammar)

            for sentence in nltk.sent_tokenize(text):
                tokens = nltk.word_tokenize(sentence)
                tagged = nltk.pos_tag(tokens)
                tree = chunk_parser.parse(tagged)

                found = []
                for subtree in tree.subtrees(filter=lambda t: t.label() == "NP"):
                    phrase = " ".join(word for word, _ in subtree.leaves())
                    if len(phrase) > 2 and phrase.lower() not in STOPWORD_CHUNKS:
                        found.append(phrase.lower())
                phrases_by_sentence.append(_dedupe_preserving_order(found))
        except Exception:  # noqa: BLE001
            phrases_by_sentence = []

    if not any(phrases_by_sentence):
        flat = _fallback_noun_phrases(text)
        phrases_by_sentence = [flat]

    # Flatten to a node list, capped, preserving first-appearance order.
    flat_phrases = _dedupe_preserving_order(
        [p for sentence in phrases_by_sentence for p in sentence]
    )[:MAX_NODES]

    node_id_by_label = {label: f"n{i}" for i, label in enumerate(flat_phrases)}
    nodes = [{"id": nid, "label": label} for label, nid in node_id_by_label.items()]

    # Co-occurrence edges: concepts appearing in the same sentence.
    edges = []
    seen_pairs = set()
    for sentence_phrases in phrases_by_sentence:
        present = [p for p in sentence_phrases if p in node_id_by_label]
        for i in range(len(present) - 1):
            a, b = node_id_by_label[present[i]], node_id_by_label[present[i + 1]]
            pair = tuple(sorted([a, b]))
            if a != b and pair not in seen_pairs:
                seen_pairs.add(pair)
                edges.append({"source": a, "target": b, "label": "appears with"})

    return {"nodes": nodes, "edges": edges}


def extract_from_code(code: str) -> dict:
    """
    Python source. Uses the standard library's `ast` module to read the
    real structure -- classes, their methods, module-level functions, and
    which functions call which. Because this parses the actual syntax
    tree rather than pattern-matching text, the relationships it reports
    are genuinely correct, not guessed.

    Raises ValueError on a syntax error so the caller can tell the
    student their code didn't parse, rather than silently producing an
    empty map.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(f"That code couldn't be parsed as Python: {exc.msg} (line {exc.lineno})")

    nodes: list[dict] = []
    edges: list[dict] = []
    node_id_by_name: dict[str, str] = {}

    def _node_for(name: str, kind: str) -> str:
        if name not in node_id_by_name:
            nid = f"n{len(node_id_by_name)}"
            node_id_by_name[name] = nid
            nodes.append({"id": nid, "label": name, "kind": kind})
        return node_id_by_name[name]

    # Pass 1: define class/function nodes and containment edges.
    for item in ast.walk(tree):
        if isinstance(item, ast.ClassDef):
            class_id = _node_for(item.name, "class")
            for child in item.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_id = _node_for(child.name, "method")
                    edges.append({"source": class_id, "target": method_id, "label": "has method"})
            for base in item.bases:
                if isinstance(base, ast.Name):
                    base_id = _node_for(base.id, "class")
                    edges.append({"source": class_id, "target": base_id, "label": "inherits from"})

    for item in tree.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _node_for(item.name, "function")

    # Pass 2: call edges between things we already know about.
    for item in ast.walk(tree):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            caller = item.name
            if caller not in node_id_by_name:
                continue
            for call in ast.walk(item):
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                    callee = call.func.id
                    if callee in node_id_by_name and callee != caller:
                        edges.append(
                            {
                                "source": node_id_by_name[caller],
                                "target": node_id_by_name[callee],
                                "label": "calls",
                            }
                        )

    # Dedupe edges (ast.walk can revisit nested definitions).
    unique_edges = []
    seen = set()
    for e in edges:
        key = (e["source"], e["target"], e["label"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    return {"nodes": nodes[:MAX_NODES], "edges": unique_edges}


OPERATOR_LABELS = {
    "=": "equals",
    "+": "plus",
    "-": "minus",
    "*": "times",
    "/": "divided by",
    "^": "to the power",
}


def extract_from_math(formula: str) -> dict:
    """
    Formulas. Splits on operators, treating each variable/constant as a
    puzzle piece and each operator as the edge joining the two pieces
    either side of it -- so `E = m * c^2` becomes E --equals-- m --times--
    c --to the power-- 2, which is exactly the shape a student
    reassembles in the game.
    """
    # Split while KEEPING the operators, since they become edge labels.
    parts = re.split(r"([=+\-*/^])", formula)
    tokens = [p.strip() for p in parts if p.strip()]

    nodes: list[dict] = []
    edges: list[dict] = []
    node_id_by_label: dict[str, str] = {}
    ordered_operands: list[str] = []

    for token in tokens:
        if token in OPERATOR_LABELS:
            continue
        if token not in node_id_by_label:
            nid = f"n{len(node_id_by_label)}"
            node_id_by_label[token] = nid
            nodes.append({"id": nid, "label": token})
        ordered_operands.append(token)

    operand_index = 0
    for token in tokens:
        if token in OPERATOR_LABELS:
            if operand_index > 0 and operand_index < len(ordered_operands):
                left = ordered_operands[operand_index - 1]
                right = ordered_operands[operand_index]
                edges.append(
                    {
                        "source": node_id_by_label[left],
                        "target": node_id_by_label[right],
                        "label": OPERATOR_LABELS[token],
                    }
                )
        else:
            operand_index += 1

    return {"nodes": nodes[:MAX_NODES], "edges": edges}


def extract(source_text: str, source_kind: str) -> dict:
    if source_kind == "code":
        return extract_from_code(source_text)
    if source_kind == "math":
        return extract_from_math(source_text)
    return extract_from_text(source_text)
