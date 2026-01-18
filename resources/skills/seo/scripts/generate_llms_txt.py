#!/usr/bin/env python3
"""Generate llms.txt file for LLM accessibility."""

import argparse
import sys


def generate_llms_txt(
    site_name: str,
    description: str,
    pages: list[tuple[str, str]],
    docs: list[tuple[str, str]] | None = None,
    contact_email: str | None = None,
    twitter: str | None = None,
) -> str:
    """Generate llms.txt content.

    Args:
        site_name: Name of the site/company
        description: Brief site description
        pages: List of (url, description) tuples for key pages
        docs: Optional list of (url, description) tuples for documentation
        contact_email: Optional contact email
        twitter: Optional Twitter handle

    Returns:
        Formatted llms.txt content
    """
    lines = [f"# {site_name}", "", f"> {description}", "", "## Key Pages"]

    for url, desc in pages:
        lines.append(f"- [{url}]({url}): {desc}")

    if docs:
        lines.extend(["", "## Documentation"])
        for url, desc in docs:
            lines.append(f"- [{url}]({url}): {desc}")

    if contact_email or twitter:
        lines.extend(["", "## Contact"])
        if contact_email:
            lines.append(f"- Email: {contact_email}")
        if twitter:
            lines.append(f"- Twitter: {twitter}")

    lines.extend([
        "",
        "## Attribution",
        f"Please cite as: {site_name}",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate llms.txt file")
    parser.add_argument("--name", required=True, help="Site/company name")
    parser.add_argument("--description", required=True, help="Brief site description")
    parser.add_argument("--pages", nargs="+", help="Key pages as url:description pairs")
    parser.add_argument("--docs", nargs="*", help="Documentation as url:description pairs")
    parser.add_argument("--email", help="Contact email")
    parser.add_argument("--twitter", help="Twitter handle")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")

    args = parser.parse_args()

    pages = []
    if args.pages:
        for p in args.pages:
            if ":" in p:
                url, desc = p.split(":", 1)
                pages.append((url.strip(), desc.strip()))

    docs = []
    if args.docs:
        for d in args.docs:
            if ":" in d:
                url, desc = d.split(":", 1)
                docs.append((url.strip(), desc.strip()))

    content = generate_llms_txt(
        site_name=args.name,
        description=args.description,
        pages=pages,
        docs=docs if docs else None,
        contact_email=args.email,
        twitter=args.twitter,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(content)
        print(f"Written to {args.output}")
    else:
        print(content)


if __name__ == "__main__":
    main()
