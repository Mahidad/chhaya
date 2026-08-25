"""
The AI-backed half of the HLL Code Converter: translating code between
languages, and solving a problem statement from scratch. Both genuinely
need Gemini -- see the reasoning in the conversation this feature was
scoped in: generating or translating a correct, novel program isn't a
"crude" (rule-based) operation the way style *extraction* is (see
app/utils/code_style_analyzer.py, which stays AI-free on purpose).

WHY STRUCTURED JSON WITH A "mapping" FIELD: the frontend's click-a-line-
to-highlight-the-translation feature needs to know which output lines
correspond to which source lines. Naive 1:1 line matching breaks the
moment one Python line becomes three Java lines (or vice versa). Instead
of guessing that mapping after the fact, Gemini is asked to hand it back
directly as part of the same response -- it already knows the
correspondence, since it just produced both sides.

SAME MOCK-FALLBACK PATTERN AS teaching_style_service.py: no
GEMINI_API_KEY, no real call -- a clearly labeled placeholder instead, so
the rest of the pipeline (saving, status transitions, the frontend's
generating -> ready flow, click-to-highlight) can be built and tested
without a key.
"""

import json

from app.core.config import settings
from app.utils import gemini
from app.utils.exceptions import ExternalServiceError

TRANSLATE_PROMPT_TEMPLATE = """You are a programming tutor helping a student learn {target_language} by
comparing it to code they already understand. {source_language_instruction}

Translate the following source code to {target_language}, preserving its
behavior exactly. {style_instruction}

Respond with ONLY a JSON object (no markdown, no commentary) matching
exactly this shape:

{{
  "detected_source_language": "<the source language, lowercase, one of python/java/cpp/javascript/c>",
  "output_code": "<the full translated code>",
  "mapping": [
    {{"source_lines": [<start>, <end>], "output_lines": [<start>, <end>], "description": "<short phrase, e.g. 'for loop over items'>"}}
  ],
  "explanation": "<2-3 sentences on the most important syntax differences a student switching between these two languages should notice>"
}}

Line numbers are 1-indexed and count EVERY line in each version, including
blank lines and closing braces, so they line up with what's actually
rendered on screen. Cover the entire source in the mapping -- every source
line should fall inside at least one block's source_lines range.

Source code:
\"\"\"
{source_code}
\"\"\"
"""

SOLVE_PROMPT_TEMPLATE = """You are a programming tutor. A student wants to solve the following
problem in {target_language}. {style_instruction}

Problem:
\"\"\"
{problem_statement}
\"\"\"

Respond with ONLY a JSON object (no markdown, no commentary) matching
exactly this shape:

{{
  "output_code": "<a complete, correct, runnable solution in {target_language}>",
  "explanation": "<2-4 sentences on the approach taken and why>"
}}
"""


def _style_instruction(style: dict | None) -> str:
    if not style:
        return ""
    parts = [
        f"indentation of {style['indent_size']} {style['indent_style']}",
        f"{style['naming_convention']} naming for variables and functions" if style["naming_convention"] != "mixed" else None,
        f"{style['brace_style'].replace('_', ' ')} brace placement" if style.get("brace_style") else None,
        _loop_preference_phrase(style.get("loop_style")),
        _branching_preference_phrase(style.get("branching_style")),
        "flat, low-nesting logic (avoid deeply nested conditionals) rather than deeply nested blocks"
        if style.get("max_nesting_depth") is not None and style["max_nesting_depth"] <= 2
        else None,
    ]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    return "Write it matching this coding style as closely as possible: " + ", ".join(parts) + "."


def _loop_preference_phrase(loop_style: str | None) -> str | None:
    return {
        "for_dominant": "prefer for-loops over while-loops where either would work",
        "while_dominant": "prefer while-loops over for-loops where either would work",
        "comprehension_heavy": "prefer list/dict comprehensions over explicit loops where reasonable",
    }.get(loop_style)


def _branching_preference_phrase(branching_style: str | None) -> str | None:
    return {
        "ternary_heavy": "prefer ternary/conditional expressions over multi-line if/else where it stays readable",
        "switch_based": "prefer switch/match statements over long if/elif chains where applicable",
        "if_else_standard": "use standard explicit if/else blocks rather than ternaries",
    }.get(branching_style)


def _mock_translation(source_code: str, source_language: str | None, target_language: str) -> dict:
    lines = source_code.splitlines() or [""]
    return {
        "detected_source_language": source_language or "python",
        "output_code": f"// MOCK TRANSLATION (no GEMINI_API_KEY set) to {target_language}\n" + source_code,
        "mapping": [
            {"source_lines": [1, len(lines)], "output_lines": [2, len(lines) + 1],
             "description": "Mock: whole file mapped as one block"}
        ],
        "explanation": "MOCK PROFILE (no GEMINI_API_KEY set) -- set GEMINI_API_KEY in .env for a real translation.",
        "_mock": True,
    }


def _mock_solution(problem_statement: str, target_language: str) -> dict:
    return {
        "output_code": f"// MOCK SOLUTION (no GEMINI_API_KEY set) for: {problem_statement[:80]}",
        "explanation": "MOCK PROFILE (no GEMINI_API_KEY set) -- set GEMINI_API_KEY in .env for a real solution.",
        "_mock": True,
    }


def _call_gemini(prompt: str) -> dict:
    response_text = gemini.generate_text(prompt)
    text = response_text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)


def translate_code(
    *, source_code: str, source_language: str | None, target_language: str, style: dict | None = None
) -> dict:
    if not settings.GEMINI_API_KEY:
        return _mock_translation(source_code, source_language, target_language)

    source_language_instruction = (
        f"The source code is written in {source_language}."
        if source_language
        else "First, detect what language the source code is written in."
    )

    try:
        prompt = TRANSLATE_PROMPT_TEMPLATE.format(
            target_language=target_language,
            source_language_instruction=source_language_instruction,
            style_instruction=_style_instruction(style),
            source_code=source_code[:15000],
        )
        return _call_gemini(prompt)
    except Exception as exc:  # noqa: BLE001
        raise ExternalServiceError(f"Gemini code translation failed: {exc}") from exc


def solve_problem(*, problem_statement: str, target_language: str, style: dict | None = None) -> dict:
    if not settings.GEMINI_API_KEY:
        return _mock_solution(problem_statement, target_language)

    try:
        prompt = SOLVE_PROMPT_TEMPLATE.format(
            target_language=target_language,
            style_instruction=_style_instruction(style),
            problem_statement=problem_statement[:5000],
        )
        return _call_gemini(prompt)
    except Exception as exc:  # noqa: BLE001
        raise ExternalServiceError(f"Gemini problem solving failed: {exc}") from exc
