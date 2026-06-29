"""
Generic parser for all test templates.

This file acts as a dispatcher.

Instead of making the UI know how every test type works, the UI will only call:

    parse_test_from_config(docx_path, config)

Then this file will look at:

    config["parser_type"]

and decide which real parser should be used.

Examples:

    BDI
    -> parser_type = "four_option_numbered"
    -> use parse_docx(...)

    BHS
    -> parser_type = "yes_no_keyed"
    -> use parse_yes_no_keyed_docx(...)

    Ferguson loneliness test
    -> parser_type = "likert_table"
    -> use parse_likert_docx(...)

    Burnout test
    -> parser_type = "numbered_questions_with_options"
    -> use parse_likert_docx(...)

The goal is to make the app easier to extend.
Later, if we add a new test type, we only add a new config and maybe one parser,
instead of rewriting the whole UI.
"""

from school_form_app import config
from school_form_app.models import ParsedTest, GradeThreshold

# Parser for BDI-like tests.
#
# Expected Word structure:
#
#   1. Question title
#   option 1
#   option 2
#   option 3
#   option 4
#
# The scores for option 1/2/3/4 come from the JSON config.
from school_form_app.parsing.docx_parser import parse_docx

# Parser for Yes/No tests where scoring depends on the question number.
#
# Example:
#
#   Questions 1, 3, 5:
#       YES = 1
#       NO  = 0
#
#   Questions 2, 4, 6:
#       YES = 0
#       NO  = 1
from school_form_app.parsing.yes_no_keyed_parser import parse_yes_no_keyed_docx

# Parser for Likert-style tests.
#
# Likert-style means the same answer options are repeated for every question.
#
# Example 1:
#   Often = 3
#   Sometimes = 2
#   Rarely = 1
#   Never = 0
#
# Example 2:
#   Never = 0
#   Rarely = 1
#   Sometimes = 2
#   Often = 3
#   Very often = 4
from school_form_app.parsing.likert_parser import parse_likert_docx


def make_thresholds_from_config(config: dict) -> list[GradeThreshold]:
    """
    Convert threshold data from JSON config into GradeThreshold objects.

    In the JSON config, thresholds look like this:

        "thresholds": [
            {
                "min_score": 0,
                "max_score": 20,
                "label": "Low level"
            },
            {
                "min_score": 21,
                "max_score": 40,
                "label": "Medium level"
            }
        ]

    But inside the app we use the GradeThreshold dataclass:

        GradeThreshold(
            min_score=0,
            max_score=20,
            label="Low level"
        )

    This function converts raw dictionaries into real Python objects.
    """

    thresholds = []

    # config.get("thresholds", []) means:
    # - if the config has a "thresholds" key, use it;
    # - if it does not exist, use an empty list.
    #
    # This prevents the app from crashing if a config has no thresholds.
    for threshold_data in config.get("thresholds", []):
        threshold = GradeThreshold(
            min_score=int(threshold_data["min_score"]),
            max_score=int(threshold_data["max_score"]),
            label=str(threshold_data["label"]),
        )

        thresholds.append(threshold)

    return thresholds


def get_option_scores_from_config(config: dict) -> list[int]:
    """
    Extract only option scores from answer_options.

    Example JSON config:

        "answer_options": [
            {"text": "Option 1", "score": 0},
            {"text": "Option 2", "score": 1},
            {"text": "Option 3", "score": 2},
            {"text": "Option 4", "score": 3}
        ]

    The old BDI parser does not need the option text.
    It only needs:

        [0, 1, 2, 3]

    So this function extracts just the score values.
    """

    option_scores = []

    for option in config.get("answer_options", []):
        score = int(option["score"])
        option_scores.append(score)

    return option_scores


def get_question_set_from_config(
    config: dict,
    key_name: str,
) -> set[int]:
    """
    Convert a question-number list from config into a set of integers.

    Example JSON config:

        "yes_score_questions": [1, 3, 5, 6]

    This function converts it into:

        {1, 3, 5, 6}

    Why use a set?

    Because this check becomes simple and fast:

        if question_number in yes_score_questions:
            ...
    """

    question_numbers = set()

    for number in config.get(key_name, []):
        question_numbers.add(int(number))

    return question_numbers


def parse_four_option_numbered_test(
    docx_path: str,
    config: dict,
) -> ParsedTest:
    """
    Parse BDI-like tests with four answer options.

    Expected Word format:

        1. Mood
        I do not feel sad
        I feel sad
        I am sad all the time
        I am so sad that I cannot stand it

    The option scores are stored in the JSON config.

    Example:

        answer_options:
            option 1 -> 0
            option 2 -> 1
            option 3 -> 2
            option 4 -> 3

    This function uses the already existing parse_docx(...) parser.
    """

    option_scores = get_option_scores_from_config(config)

    parsed_test = parse_docx(
        path=docx_path,
        option_scores=option_scores,
    )

    return parsed_test


def parse_yes_no_keyed_test(
    docx_path: str,
    config: dict,
) -> ParsedTest:
    """
    Parse Yes/No tests with a scoring key.

    In this test type, the score depends on the question number.

    Example:

        Question 1:
            YES = 1
            NO  = 0

        Question 2:
            YES = 0
            NO  = 1

    The config stores the scoring key like this:

        "yes_score_questions": [1, 3, 5]
        "no_score_questions": [2, 4, 6]

    This function extracts those two lists and passes them to the Yes/No parser.
    """

    yes_score_questions = get_question_set_from_config(
        config=config,
        key_name="yes_score_questions",
    )

    no_score_questions = get_question_set_from_config(
        config=config,
        key_name="no_score_questions",
    )

    parsed_test = parse_yes_no_keyed_docx(
        path=docx_path,
        yes_score_questions=yes_score_questions,
        no_score_questions=no_score_questions,
    )

    return parsed_test


def parse_likert_test(
    docx_path: str,
    config: dict,
) -> ParsedTest:
    """
    Parse Likert-style tests.

    Likert-style means that every question has the same answer options.

    Example 1: Ferguson loneliness test

        Often = 3
        Sometimes = 2
        Rarely = 1
        Never = 0

    Example 2: Burnout test

        Never = 0
        Rarely = 1
        Sometimes = 2
        Often = 3
        Very often = 4

    The exact answer labels and scores are stored inside the JSON config.

    This function does not manually process the options.
    It passes the whole config into parse_likert_docx(...).
    """

    parsed_test = parse_likert_docx(
        docx_path=docx_path,
        config=config,
    )

    return parsed_test


def parse_test_from_config(
    docx_path: str,
    config: dict,
) -> ParsedTest:
    """
    Parse a Word test using a JSON test template.

    This is the main function of this file.

    The UI should call this function later instead of directly calling:

        parse_docx(...)
        parse_yes_no_keyed_docx(...)
        parse_likert_docx(...)

    Input:
        docx_path:
            Path to the selected Word file.

        config:
            Test template loaded from JSON.

    Output:
        ParsedTest object.

    Example usage:

        config = find_config_by_id("ferguson_loneliness")

        parsed_test = parse_test_from_config(
            docx_path="Тест Фергюсон.docx",
            config=config,
        )

    Supported parser types:

        four_option_numbered
            For BDI-like tests.

        yes_no_keyed
            For BHS-like tests.

        likert_table
            For table-based Likert tests like Ferguson.

        numbered_questions_with_options
            For numbered paragraph Likert tests like burnout.
    """

    parser_type = config.get("parser_type")

    if not parser_type:
        raise ValueError(
            "Config does not contain parser_type."
        )

    # Case 1:
    # BDI-like test.
    #
    # The Word file contains questions and four answer options per question.
    if parser_type == "four_option_numbered":
        parsed_test = parse_four_option_numbered_test(
            docx_path=docx_path,
            config=config,
        )

    # Case 2:
    # BHS-like test.
    #
    # The Word file contains Yes/No questions.
    # The score is decided by a question-number key.
    elif parser_type == "yes_no_keyed":
        parsed_test = parse_yes_no_keyed_test(
            docx_path=docx_path,
            config=config,
        )

    # Case 3:
    # Likert-style tests.
    #
    # These tests use the same answer options for all questions.
    #
    # Examples:
    #   Ferguson loneliness test
    #   Burnout test
    elif parser_type in [
        "likert_table",
        "numbered_questions_with_options",
    ]:
        parsed_test = parse_likert_test(
            docx_path=docx_path,
            config=config,
        )

    # If parser_type is unknown, stop immediately.
    #
    # This is safer than guessing, because guessing could create a wrong form
    # and wrong scoring.
    else:
        raise ValueError(
            f"Unknown parser_type: {parser_type}"
        )

    # At this point, parsed_test already contains:
    #
    #   parsed_test.title
    #   parsed_test.instructions
    #   parsed_test.questions
    #
    # But thresholds should come from the JSON config, not from the Word file.
    # So we attach thresholds here.
    # At this point, parsed_test already contains:
#
#   parsed_test.title
#   parsed_test.instructions
#   parsed_test.questions
#
# However, Word files are not always clean.
# Sometimes the first readable paragraph is not the real title.
#
# Since our JSON config already contains the correct test name,
# we prefer config["name"] as the final title.
    if config.get("name"):
        parsed_test.title = str(config["name"])

# Thresholds should come from the JSON config, not from the Word file.
    parsed_test.thresholds = make_thresholds_from_config(config)

    return parsed_test