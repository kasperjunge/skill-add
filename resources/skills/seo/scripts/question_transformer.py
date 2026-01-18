#!/usr/bin/env python3
"""Transform keywords into questions for AEO optimization."""

import argparse


# Question patterns for different intent types
QUESTION_PATTERNS = {
    "informational": [
        "What is {keyword}?",
        "How does {keyword} work?",
        "What are the benefits of {keyword}?",
        "Why is {keyword} important?",
        "What are the best practices for {keyword}?",
    ],
    "comparison": [
        "What is the best {keyword}?",
        "{keyword} vs alternatives: which is better?",
        "How to choose the right {keyword}?",
        "What are the top {keyword} options?",
        "Which {keyword} should I use?",
    ],
    "howto": [
        "How to use {keyword}?",
        "How to set up {keyword}?",
        "How to implement {keyword}?",
        "How to get started with {keyword}?",
        "Step-by-step guide to {keyword}",
    ],
    "troubleshooting": [
        "Why is {keyword} not working?",
        "How to fix {keyword} issues?",
        "Common {keyword} problems and solutions",
        "{keyword} troubleshooting guide",
        "How to debug {keyword}?",
    ],
    "cost": [
        "How much does {keyword} cost?",
        "Is {keyword} worth the price?",
        "{keyword} pricing comparison",
        "Free alternatives to {keyword}?",
        "What is the ROI of {keyword}?",
    ],
}


def transform_keyword(keyword: str, intent_types: list[str] | None = None) -> list[str]:
    """Transform a keyword into relevant questions.

    Args:
        keyword: The keyword to transform
        intent_types: Optional list of intent types to use. If None, uses all types.

    Returns:
        List of questions
    """
    questions = []

    types_to_use = intent_types or list(QUESTION_PATTERNS.keys())

    for intent_type in types_to_use:
        if intent_type in QUESTION_PATTERNS:
            for pattern in QUESTION_PATTERNS[intent_type]:
                questions.append(pattern.format(keyword=keyword))

    return questions


def generate_follow_up_questions(keyword: str, base_question: str) -> list[str]:
    """Generate follow-up questions users might ask.

    Args:
        keyword: The main keyword
        base_question: The initial question

    Returns:
        List of follow-up questions
    """
    follow_ups = [
        f"What are the alternatives to {keyword}?",
        f"What should I know before using {keyword}?",
        f"What are common mistakes with {keyword}?",
        f"How long does it take to learn {keyword}?",
        f"What tools do I need for {keyword}?",
        f"Is {keyword} suitable for beginners?",
        f"What are advanced {keyword} techniques?",
        f"How to measure {keyword} success?",
    ]
    return follow_ups


def main():
    parser = argparse.ArgumentParser(
        description="Transform keywords into questions for AEO"
    )
    parser.add_argument("keywords", nargs="+", help="Keywords to transform")
    parser.add_argument(
        "--intents",
        nargs="+",
        choices=list(QUESTION_PATTERNS.keys()),
        help="Specific intent types to generate",
    )
    parser.add_argument(
        "--follow-ups",
        action="store_true",
        help="Include follow-up questions",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output as markdown",
    )
    parser.add_argument("-o", "--output", help="Output file")

    args = parser.parse_args()

    output_lines = []

    for keyword in args.keywords:
        if args.markdown:
            output_lines.append(f"## {keyword.title()}")
            output_lines.append("")
        else:
            output_lines.append(f"Keyword: {keyword}")
            output_lines.append("-" * 40)

        questions = transform_keyword(keyword, args.intents)

        if args.markdown:
            output_lines.append("### Primary Questions")
            for q in questions:
                output_lines.append(f"- {q}")
        else:
            output_lines.append("Questions:")
            for q in questions:
                output_lines.append(f"  - {q}")

        if args.follow_ups:
            follow_ups = generate_follow_up_questions(keyword, questions[0] if questions else "")
            if args.markdown:
                output_lines.append("")
                output_lines.append("### Follow-up Questions")
                for q in follow_ups:
                    output_lines.append(f"- {q}")
            else:
                output_lines.append("\nFollow-up Questions:")
                for q in follow_ups:
                    output_lines.append(f"  - {q}")

        output_lines.append("")

    output = "\n".join(output_lines)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
