from quiz_formatter.parser import parse_questions


def test_parse_questions_handles_multiline_prompts_and_options():
    raw_text = """
    1. First line of the question
    second line of the question

    • first option
    • second option
    √ correct option
    • final

    2. Another question
    • option one
    √ option two continues
    on the next line
    • option three
    """

    questions = parse_questions(raw_text)

    assert len(questions) == 2

    assert questions[0].number == 1
    assert questions[0].prompt == "First line of the question second line of the question"
    assert questions[0].correct_index == 2
    assert questions[0].options[2] == "correct option"

    assert questions[1].number == 2
    assert questions[1].correct_index == 1
    assert questions[1].options[1] == "option two continues on the next line"


def test_parse_questions_skips_incomplete_blocks():
    raw_text = """
    1. Missing correct answer
    • option one
    • option two

    2. Valid question
    • option one
    √ option two
    """

    questions = parse_questions(raw_text)

    assert len(questions) == 1
    assert questions[0].number == 2
