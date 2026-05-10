from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import QuizResult
from .quiz import label_for_option, score_results

DEFAULT_HISTORY_PATH = Path(".quiz-cache/history.jsonl")


def save_history(
    results: list[QuizResult],
    pdf_name: str,
    count: int,
    seed: int | None,
    shuffle_answers: bool,
    mode: str,
    history_path: str | Path = DEFAULT_HISTORY_PATH,
) -> dict[str, Any]:
    history_file = Path(history_path)
    history_file.parent.mkdir(parents=True, exist_ok=True)

    correct, total = score_results(results)
    percentage = (correct / total) * 100 if total else 0
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pdf_name": pdf_name,
        "count": count,
        "seed": seed,
        "shuffle_answers": shuffle_answers,
        "mode": mode,
        "score": {
            "correct": correct,
            "total": total,
            "percentage": round(percentage, 1),
        },
        "incorrect_questions": [
            _serialize_result(result) for result in results if not result.is_correct
        ],
    }

    with history_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def load_history(
    history_path: str | Path = DEFAULT_HISTORY_PATH,
    limit: int = 10,
) -> list[dict[str, Any]]:
    history_file = Path(history_path)
    if not history_file.exists():
        return []

    entries: list[dict[str, Any]] = []
    with history_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return list(reversed(entries[-limit:]))


def _serialize_result(result: QuizResult) -> dict[str, Any]:
    question = result.question
    selected_index = result.selected_index
    correct_index = question.correct_index

    return {
        "question_number": question.number,
        "prompt": question.prompt,
        "selected_label": label_for_option(selected_index) if selected_index is not None else None,
        "selected_text": question.options[selected_index] if selected_index is not None else None,
        "correct_label": label_for_option(correct_index),
        "correct_text": question.options[correct_index],
    }
