"""
The AI-backed generation layer for Code Studio's Visualizer. Same
mock-fallback shape as code_conversion_service.py and
teaching_style_service.py -- no GEMINI_API_KEY, no real call, a clearly
labeled placeholder trace instead.

WHY THE PROMPT IS SHAPED THE WAY IT IS: this is a simulated trace, not a
real sandboxed execution (see the conversation this feature was scoped
in -- real execution across 5 languages needs sandboxing infrastructure
this project doesn't have yet). Given that constraint, the prompt is
written to get as close to "actually correct" as prompting can achieve:

1. TWO-PASS INSTRUCTION. The model is told to silently compute the real
   execution result first (like actually running the program in its
   head), and only then narrate that already-computed execution as
   steps -- rather than generating plausible-looking steps on the fly,
   which is where a model is most likely to drift from what the code
   actually does, especially around arithmetic and loop bounds.
2. ONE STEP PER LINE ACTUALLY EXECUTED, not per line of source. A loop
   that runs 5 times must produce 5 steps -- this is explicitly called
   out because collapsing a loop into one summarized step is a common
   failure mode and it's exactly the part a student most needs to see
   iterate.
3. A bounded cap (first 4 / last 2, with a marker step in between) for
   loops that would otherwise produce huge traces -- keeps output usable
   without asking the model to truncate its own reasoning early, which
   would risk it losing track of state.
"""

import json

from app.core.config import settings
from app.utils import gemini
from app.utils.exceptions import ExternalServiceError

VISUALIZE_PROMPT_TEMPLATE = """You are simulating the EXACT execution of the following {language} program,
one step at a time, the way a debugger would. Accuracy is the only thing
that matters here -- a student is relying on this trace to understand what
the code truly does.

Work through this in two passes, silently, before producing your answer:

PASS 1: Mentally execute the entire program for real, computing the actual
final output and every intermediate variable value, the way an interpreter
would. Do the arithmetic and comparisons precisely -- never estimate,
round, or guess a value.

PASS 2: Walk back through that same execution and write down one step per
LINE ACTUALLY EXECUTED, in true run order -- not per line of source code.
A line inside a loop that runs 5 times produces 5 separate steps, one per
iteration, each with that iteration's own variable values. A conditional
only produces steps for the branch actually taken. A recursive call
produces its own nested steps in the order they really run.

Rules:
- If a single loop would produce more than 15 steps, show the first 4
  iterations and the last 2 in full detail, and insert exactly one step
  with "line": -1 whose description states how many iterations were
  skipped in between. Every OTHER loop must be fully expanded, one step
  per iteration -- do not summarize a short loop.
- Every variable in scope at that point must appear in "variables" with
  its exact current value (as a string), not just the ones that changed.
- A function call gets a step entering it (parameters bound to their
  argument values) and a separate step for its return value.

Respond with ONLY a JSON object (no markdown, no commentary) matching
exactly this shape:

{{
  "steps": [
    {{"line": <1-indexed line number, or -1 for a skipped-iterations marker>, "variables": {{"<name>": "<value as a string>"}}, "description": "<one short phrase of what this step just did>"}}
  ],
  "explanation": "<2-3 sentences on what this program computes overall and its final result>"
}}

Source code ({language}):
\"\"\"
{source_code}
\"\"\"
"""


def _mock_trace(source_code: str, language: str) -> dict:
    lines = source_code.splitlines() or [""]
    return {
        "steps": [
            {
                "line": 1,
                "variables": {},
                "description": "MOCK TRACE (no GEMINI_API_KEY set) -- this is a placeholder, not a real trace.",
            },
            {
                "line": min(2, len(lines)),
                "variables": {"example": "0"},
                "description": "Set GEMINI_API_KEY in .env to see a real step-by-step trace here.",
            },
        ],
        "explanation": "MOCK PROFILE (no GEMINI_API_KEY set) -- set GEMINI_API_KEY in .env for a real trace.",
        "_mock": True,
    }


def generate_trace(*, source_code: str, language: str) -> dict:
    if not settings.GEMINI_API_KEY:
        return _mock_trace(source_code, language)

    try:
        prompt = VISUALIZE_PROMPT_TEMPLATE.format(language=language, source_code=source_code[:8000])
        response_text = gemini.generate_text(prompt)
        text = response_text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(text)
    except Exception as exc:  # noqa: BLE001
        raise ExternalServiceError(f"Gemini trace generation failed: {exc}") from exc
