from __future__ import annotations

import re

from .models import Question

QUESTION_PATTERN = re.compile(r"^\s*(\d+)\.\s*(.+)?$")
OPTION_PREFIXES = ("•", "√")
CORRECT_PREFIX = "√"


def parse_questions(raw_text: str) -> list[Question]:
    lines = [_normalize_line(line) for line in raw_text.splitlines()]

    questions: list[Question] = []
    current_question_number: int | None = None
    prompt_parts: list[str] = []
    options: list[str] = []
    correct_index: int | None = None
    last_option_index: int | None = None

    def finalize_current() -> None:
        nonlocal current_question_number, prompt_parts, options, correct_index, last_option_index

        if current_question_number is None:
            return

        cleaned_prompt = _collapse_parts(prompt_parts)
        cleaned_options = [_collapse_parts([option]) for option in options if option.strip()]

        if cleaned_prompt and cleaned_options and correct_index is not None:
            questions.append(
                Question(
                    number=current_question_number,
                    prompt=cleaned_prompt,
                    options=cleaned_options,
                    correct_index=correct_index,
                )
            )

        current_question_number = None
        prompt_parts = []
        options = []
        correct_index = None
        last_option_index = None

    for line in lines:
        if not line:
            continue

        question_match = QUESTION_PATTERN.match(line)
        if question_match:
            finalize_current()
            current_question_number = int(question_match.group(1))
            trailing_prompt = (question_match.group(2) or "").strip()
            prompt_parts = [trailing_prompt] if trailing_prompt else []
            continue

        if current_question_number is None:
            continue

        if line.startswith(OPTION_PREFIXES):
            is_correct = line.startswith(CORRECT_PREFIX)
            option_text = line[1:].strip()
            options.append(option_text)
            last_option_index = len(options) - 1
            if is_correct:
                correct_index = last_option_index
            continue

        if last_option_index is not None:
            options[last_option_index] = f"{options[last_option_index]} {line}".strip()
            continue

        prompt_parts.append(line)

    finalize_current()
    return questions


def _normalize_line(line: str) -> str:
    line = line.replace("\uf0b7", "•")
    line = line.replace("\u221a", "√")
    line = re.sub(r"\s+", " ", line.strip())
    return line


def _collapse_parts(parts: list[str]) -> str:
    text = " ".join(part.strip() for part in parts if part.strip())
    return re.sub(r"\s+", " ", text).strip()
