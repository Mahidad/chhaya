"""
The Gemini-calling layer for Code Studio's Practice tab: matching saved
work to relevant problems, and judging a submission.

Same mock-fallback pattern as every other AI service in this app -- no
GEMINI_API_KEY, no real call, a clearly labeled placeholder instead so
the rest of the pipeline stays testable.

ON JUDGING ACCURACY: this reads the code and reasons about it rather than
executing it against test cases (real execution needs sandboxing
infrastructure this project doesn't have -- same constraint as the
Visualizer). The prompt is therefore written to force the model to
actually trace the logic on concrete inputs before ruling, rather than
pattern-matching "this looks like a correct solution", which is where a
model is most likely to wave through subtly broken code.
"""

import json

from app.core.config import settings
from app.utils import gemini
from app.utils.exceptions import ExternalServiceError

MATCH_PROMPT_TEMPLATE = """A student has been working on the code below. Recommend which practice
problems from the provided list would be most useful for them next.

Pick problems that exercise the same underlying concepts and data
structures as the student's work -- not merely problems whose wording is
superficially similar. If the student's code is about graph traversal,
prefer other graph-traversal problems even if the surface topic differs.

Student's recent work:
\"\"\"
{work_summary}
\"\"\"

Available problems (title_slug :: title :: topic tags):
{problem_list}

Respond with ONLY a JSON object (no markdown, no commentary):

{{
  "picks": [
    {{"title_slug": "<exact slug from the list above>", "reason": "<one short phrase on why this fits their work>"}}
  ]
}}

Choose at most {limit}. Use only slugs that appear in the list above -- never invent one.
"""

JUDGE_PROMPT_TEMPLATE = """You are grading a student's solution to a programming problem. Be rigorous:
a wrong answer marked correct actively misleads them.

Before ruling, work through this silently:
1. Read the problem's requirements and note every constraint and edge case.
2. Trace the student's code line by line on a normal input, computing the
   real result -- do not assume it works because it looks conventional.
3. Trace it again on edge cases: empty input, a single element, duplicates,
   the smallest and largest values the constraints allow, and any case the
   problem statement calls out specifically.
4. Only then decide correctness. If ANY traced case produces a wrong
   result or crashes, it is not correct.

Problem:
\"\"\"
{problem_description}
\"\"\"

Student's solution ({language}):
\"\"\"
{submitted_code}
\"\"\"

Respond with ONLY a JSON object (no markdown, no commentary):

{{
  "is_correct": true | false,
  "feedback": "<2-4 sentences. If wrong, name the specific failing case and why. If correct, note one thing they did well and any improvement worth making.>",
  "time_complexity": "<Big-O of the runtime, e.g. O(n log n)>",
  "space_complexity": "<Big-O of the extra space used, excluding the output>"
}}
"""


def _call_gemini(prompt: str) -> dict:
    response_text = gemini.generate_text(prompt)
    text = response_text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)


def match_problems(*, work_summary: str, problems: list, limit: int) -> list[dict]:
    """Returns [{"title_slug": ..., "reason": ...}, ...]."""
    if not settings.GEMINI_API_KEY:
        # Mock: just take the first `limit` problems so the flow stays testable.
        return [
            {"title_slug": p.title_slug, "reason": "MOCK MATCH (no GEMINI_API_KEY set)"}
            for p in problems[:limit]
        ]

    problem_list = "\n".join(
        f"{p.title_slug} :: {p.title} :: {', '.join(p.topic_tags or [])}" for p in problems
    )

    try:
        prompt = MATCH_PROMPT_TEMPLATE.format(
            work_summary=work_summary[:8000], problem_list=problem_list[:12000], limit=limit
        )
        result = _call_gemini(prompt)
        return result.get("picks") or []
    except Exception as exc:  # noqa: BLE001
        raise ExternalServiceError(f"Gemini problem matching failed: {exc}") from exc


def judge_submission(*, problem_description: str, submitted_code: str, language: str) -> dict:
    if not settings.GEMINI_API_KEY:
        return {
            "is_correct": True,
            "feedback": "MOCK VERDICT (no GEMINI_API_KEY set) -- set GEMINI_API_KEY in .env for a real review.",
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "_mock": True,
        }

    try:
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            problem_description=problem_description[:8000],
            submitted_code=submitted_code[:8000],
            language=language,
        )
        return _call_gemini(prompt)
    except Exception as exc:  # noqa: BLE001
        raise ExternalServiceError(f"Gemini submission judging failed: {exc}") from exc
