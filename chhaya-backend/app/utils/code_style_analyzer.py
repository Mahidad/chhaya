"""
Extracts a coder's style from a sample of their code -- pure regex and
counting, deliberately NOT an AI call. Unlike code translation (see
code_conversion_service.py, which genuinely needs Gemini), "how is this
code indented, and what does this person call their variables" is fully
answerable by looking at characters, which makes it the one half of the
HLL Code Converter feature that's reproducible by hand in the no-AI exam.

Every function here is a pure function: text in, a plain value out. No DB,
no request objects -- easy to test in isolation (and tested that way
during development; see the docstring in code_style_profile_service.py
for the sample this was checked against).
"""

import re
from collections import Counter

COMMENT_PREFIXES = {
    "python": ("#",),
    "java": ("//",),
    "cpp": ("//",),
    "javascript": ("//",),
    "c": ("//",),
}

# Python has no braces; brace-style detection is skipped for it.
BRACE_LANGUAGES = {"java", "cpp", "javascript", "c"}


def _leading_whitespace(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t"))]


def detect_indent(lines: list[str]) -> tuple[str, int]:
    """
    Returns (indent_style, indent_size). indent_style is "tabs" or
    "spaces"; indent_size is spaces-per-level (1 for tabs, since a tab is
    one indent unit regardless of how wide it renders).

    Heuristic: look at every indented line's leading whitespace. If tabs
    appear at all, call it tabs. Otherwise, the smallest positive number
    of leading spaces seen across the sample is taken as one indent level
    -- simple, and right far more often than not for consistently
    formatted code, which is the only kind this feature is trying to
    learn from anyway.
    """
    space_counts = []
    for line in lines:
        ws = _leading_whitespace(line)
        if not ws:
            continue
        if "\t" in ws:
            return "tabs", 1
        space_counts.append(len(ws))

    if not space_counts:
        return "spaces", 4  # no indentation observed at all -- reasonable default

    return "spaces", min(space_counts)


IDENTIFIER_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:=(?!=)|\()")


def _classify_identifier(name: str) -> str | None:
    if "_" in name and name.islower():
        return "snake_case"
    if "_" in name and name.isupper():
        return None  # CONSTANT_CASE -- excluded, not a style choice most people vary
    if name[0].isupper():
        return "PascalCase"
    if name[0].islower() and any(c.isupper() for c in name):
        return "camelCase"
    return None  # single lowercase word etc. -- ambiguous, doesn't count either way


def detect_naming_convention(code: str) -> str:
    """
    Looks at every identifier immediately followed by "=" (an assignment
    target) or "(" (a function/method call or definition), classifies
    each as snake_case / camelCase / PascalCase, and returns whichever is
    most common. Falls back to "mixed" when there's no clear majority
    (e.g. genuinely inconsistent code, or too short a sample to tell).
    """
    votes = Counter()
    for match in IDENTIFIER_RE.finditer(code):
        label = _classify_identifier(match.group(1))
        if label:
            votes[label] += 1

    if not votes:
        return "mixed"

    (top_label, top_count), *rest = votes.most_common()
    runner_up_count = rest[0][1] if rest else 0
    # Require a real majority, not just "happened to have one more" --
    # otherwise a 3-line sample calls "mixed" code confidently one way or
    # the other on what's really a coin flip.
    if top_count >= 2 * max(runner_up_count, 1) or (runner_up_count == 0 and top_count >= 2):
        return top_label
    return "mixed"


def detect_brace_style(lines: list[str], language: str) -> str | None:
    """
    "same_line" (`if (x) {`, aka K&R/1TBS) vs "next_line" (`{` alone on
    its own line, aka Allman). None for languages without braces.
    """
    if language not in BRACE_LANGUAGES:
        return None

    same_line = next_line = 0
    for line in lines:
        stripped = line.strip()
        if stripped == "{":
            next_line += 1
        elif stripped.endswith("{") and len(stripped) > 1:
            same_line += 1

    if same_line == 0 and next_line == 0:
        return None
    return "same_line" if same_line >= next_line else "next_line"


# ---------------------------------------------------------------------------
# Loops, branching, and complexity -- all still plain counting, no AI.
# Patterns are intentionally per-language rather than one generic regex:
# Python's `for x in y:` and Java's `for (int i = 0; ...)` don't share
# enough structure for one pattern to catch both reliably, and a wrong
# count here would silently misrepresent someone's style rather than
# fail loudly, which is worse than the extra per-language branching.
# ---------------------------------------------------------------------------

_LOOP_PATTERNS = {
    "python": {"for": re.compile(r"^\s*for\s+\S+\s+in\s+"), "while": re.compile(r"^\s*while\s")},
    "java": {"for": re.compile(r"\bfor\s*\("), "while": re.compile(r"\bwhile\s*\(")},
    "cpp": {"for": re.compile(r"\bfor\s*\("), "while": re.compile(r"\bwhile\s*\(")},
    "c": {"for": re.compile(r"\bfor\s*\("), "while": re.compile(r"\bwhile\s*\(")},
    "javascript": {"for": re.compile(r"\bfor\s*\("), "while": re.compile(r"\bwhile\s*\(")},
}
# A Python comprehension on one line: `[... for x in y ...]` / `{...}` / `(...)`.
# Crude on purpose -- catches the common single-line case, not multi-line
# comprehensions, which is a reasonable trade-off for "what's this
# person's usual habit" rather than "count every comprehension exactly".
_COMPREHENSION_RE = re.compile(r"[\[\{(][^\[\]{}()]*\bfor\b[^\[\]{}()]*\bin\b[^\[\]{}()]*[\]\})]")

_BRANCH_PATTERNS = {
    "python": {
        "if": re.compile(r"^\s*(if|elif)\s", re.MULTILINE),
        "ternary": re.compile(r"\S+\s+if\s+.+\s+else\s+\S+"),
        "switch": re.compile(r"^\s*match\s+\S+:", re.MULTILINE),  # Python 3.10+ structural pattern matching
    },
}
_C_FAMILY_BRANCH = {
    "if": re.compile(r"\b(if|else\s+if)\s*\("),
    "ternary": re.compile(r"[^?:]+\?[^?:]+:[^;{}]+"),
    "switch": re.compile(r"\bswitch\s*\("),
}
for _lang in ("java", "cpp", "c", "javascript"):
    _BRANCH_PATTERNS[_lang] = _C_FAMILY_BRANCH

# Decision points counted toward cyclomatic complexity -- the standard
# McCabe approximation (1 + number of decision points), computed for the
# WHOLE sample rather than per-function: reliably finding function
# boundaries with regex across 5 languages (especially C++/JS, which
# don't have one canonical function-definition shape) is fragile enough
# to be worse than not attempting it. A whole-sample score still answers
# "does this person tend to write branchy/nested code or straight-line
# code", which is the actual style signal being looked for.
_COMPLEXITY_KEYWORDS = {
    "python": re.compile(r"\b(if|elif|for|while|except)\b|(\band\b)|(\bor\b)"),
    "java": re.compile(r"\b(if|for|while|case|catch)\b|(&&)|(\|\|)|(\?)"),
    "cpp": re.compile(r"\b(if|for|while|case|catch)\b|(&&)|(\|\|)|(\?)"),
    "c": re.compile(r"\b(if|for|while|case)\b|(&&)|(\|\|)|(\?)"),
    "javascript": re.compile(r"\b(if|for|while|case|catch)\b|(&&)|(\|\|)|(\?)"),
}


def detect_loop_style(code: str, language: str) -> str:
    patterns = _LOOP_PATTERNS.get(language, _LOOP_PATTERNS["java"])
    for_count = sum(1 for line in code.splitlines() if patterns["for"].search(line))
    while_count = sum(1 for line in code.splitlines() if patterns["while"].search(line))
    comprehension_count = len(_COMPREHENSION_RE.findall(code)) if language == "python" else 0

    total = for_count + while_count + comprehension_count
    if total == 0:
        return "none"
    if language == "python" and comprehension_count > (for_count + while_count):
        return "comprehension_heavy"
    # Zero of one kind is unambiguous regardless of how few of the other
    # kind exist -- one for-loop and no while-loops is clearly
    # for-dominant, not "not enough evidence".
    if while_count == 0:
        return "for_dominant"
    if for_count == 0:
        return "while_dominant"
    if for_count >= 2 * while_count:
        return "for_dominant"
    if while_count >= 2 * for_count:
        return "while_dominant"
    return "mixed"


def detect_branching_style(code: str, language: str) -> str:
    patterns = _BRANCH_PATTERNS.get(language, _C_FAMILY_BRANCH)
    if_count = len(patterns["if"].findall(code))
    ternary_count = len(patterns["ternary"].findall(code))
    switch_count = len(patterns["switch"].findall(code))

    total = if_count + ternary_count
    if total == 0 and switch_count == 0:
        return "none"
    if switch_count > 0 and switch_count >= if_count:
        return "switch_based"
    if ternary_count > 0 and ternary_count >= if_count:
        return "ternary_heavy"
    return "if_else_standard"


def compute_complexity(code: str, language: str, lines: list[str]) -> dict:
    """
    Returns {"cyclomatic_complexity": int, "max_nesting_depth": int}.
    Cyclomatic complexity: 1 + count of decision-point keywords/operators
    across the whole sample (McCabe's approximation). Nesting depth: the
    deepest indentation level observed, in indent-units (not raw spaces)
    -- a second, independent signal for "how structurally nested does
    this person's code tend to get", since a file can have high
    cyclomatic complexity from many short flat conditionals just as
    easily as from deep nesting, and those are different style traits.
    """
    keyword_re = _COMPLEXITY_KEYWORDS.get(language, _COMPLEXITY_KEYWORDS["java"])
    decision_points = sum(len(keyword_re.findall(line)) for line in lines)

    indent_style, indent_size = detect_indent(lines)
    unit_len = 1 if indent_style == "tabs" else max(indent_size, 1)
    unit_char = "\t" if indent_style == "tabs" else " "
    max_depth = 0
    for line in lines:
        ws = _leading_whitespace(line)
        if unit_char == "\t":
            depth = ws.count("\t")
        else:
            depth = len(ws) // unit_len
        max_depth = max(max_depth, depth)

    return {"cyclomatic_complexity": 1 + decision_points, "max_nesting_depth": max_depth}


def analyze_code_style(code: str, language: str) -> dict:
    """
    The one function everything else in this module builds up to.
    Returns a plain dict matching CodeStyleProfile's fields (minus the
    id/user_id/label bookkeeping the repository adds).
    """
    language = language.lower()
    all_lines = code.splitlines()
    non_blank_lines = [line for line in all_lines if line.strip()]

    indent_style, indent_size = detect_indent(non_blank_lines)
    naming_convention = detect_naming_convention(code)
    brace_style = detect_brace_style(non_blank_lines, language)
    loop_style = detect_loop_style(code, language)
    branching_style = detect_branching_style(code, language)
    complexity = compute_complexity(code, language, non_blank_lines)

    comment_prefixes = COMMENT_PREFIXES.get(language, ("#", "//"))
    comment_lines = sum(
        1 for line in non_blank_lines if line.strip().startswith(comment_prefixes)
    )

    total_lines = len(all_lines) or 1
    blank_lines = total_lines - len(non_blank_lines)

    return {
        "indent_style": indent_style,
        "indent_size": indent_size,
        "naming_convention": naming_convention,
        "brace_style": brace_style,
        "loop_style": loop_style,
        "branching_style": branching_style,
        "cyclomatic_complexity": complexity["cyclomatic_complexity"],
        "max_nesting_depth": complexity["max_nesting_depth"],
        "comment_density": round(comment_lines / len(non_blank_lines), 3) if non_blank_lines else 0.0,
        "avg_line_length": round(sum(len(l) for l in non_blank_lines) / len(non_blank_lines), 1) if non_blank_lines else 0.0,
        "blank_line_frequency": round(blank_lines / total_lines, 3),
    }


def apply_style(code: str, style: dict) -> str:
    """
    Crude, SAFE style enforcement on top of Gemini's output -- whitespace-
    only transformations that can't change what the code does:
    re-indenting to the target indent_style/size, and normalizing brace
    placement. Deliberately does NOT attempt to rename identifiers to
    match a naming_convention -- renaming safely requires knowing which
    occurrences of a token are the same identifier versus a coincidental
    match (e.g. a local variable `data` vs an unrelated string "data"),
    which a regex pass cannot determine reliably. Gemini is asked to
    apply the naming convention itself as part of generation instead (see
    the prompt in code_conversion_service.py) -- it has the whole-program
    context a blind find/replace doesn't.
    """
    lines = code.splitlines()
    if not lines:
        return code

    # Re-indent: measure each line's indent DEPTH in the original file's
    # units, then re-render at the target indent size/style.
    original_indent_style, original_indent_size = detect_indent(lines)
    unit = "\t" if original_indent_style == "tabs" else " " * max(original_indent_size, 1)
    target_unit = "\t" if style.get("indent_style") == "tabs" else " " * style.get("indent_size", 4)

    reindented = []
    for line in lines:
        ws = _leading_whitespace(line)
        depth = ws.count(unit) if unit and ws else 0
        reindented.append(target_unit * depth + line.lstrip(" \t"))

    return "\n".join(reindented)
