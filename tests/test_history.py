import json

from quiz_formatter.history import load_history, save_history
from quiz_formatter.models import PresentedQuestion, Question, QuizResult


def test_save_history_and_load_recent_entries(tmp_path):
    history_path = tmp_path / "history.jsonl"
    question = Question(
        number=7,
        prompt="Prompt",
        options=["Alpha", "Bravo", "Charlie"],
        correct_index=1,
    )
    presented = PresentedQuestion(
        source=question,
        options=["Charlie", "Bravo", "Alpha"],
        correct_index=1,
    )
    result = QuizResult(question=presented, selected_index=0)

    entry = save_history(
        results=[result],
        pdf_name="sample.pdf",
        count=10,
        seed=99,
        shuffle_answers=True,
        mode="cli",
        history_path=history_path,
    )

    assert entry["score"]["correct"] == 0
    assert entry["incorrect_questions"][0]["correct_text"] == "Bravo"

    loaded = load_history(history_path, limit=5)
    assert len(loaded) == 1
    assert loaded[0]["pdf_name"] == "sample.pdf"

    with history_path.open("r", encoding="utf-8") as handle:
        persisted = json.loads(handle.readline())
    assert persisted["count"] == 10
