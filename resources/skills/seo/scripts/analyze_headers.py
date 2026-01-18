#!/usr/bin/env python3
"""Analyze header structure from HTML content."""

import argparse
import re
import sys
from html.parser import HTMLParser


class HeaderExtractor(HTMLParser):
    """Extract headers from HTML."""

    def __init__(self):
        super().__init__()
        self.headers = []
        self.current_header = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.current_header = tag
            self.current_text = []

    def handle_endtag(self, tag):
        if tag == self.current_header:
            text = " ".join(self.current_text).strip()
            self.headers.append((self.current_header, text))
            self.current_header = None
            self.current_text = []

    def handle_data(self, data):
        if self.current_header:
            self.current_text.append(data.strip())


def analyze_headers(html_content: str) -> dict:
    """Analyze header structure and return analysis.

    Returns:
        Dict with headers, issues, and recommendations
    """
    parser = HeaderExtractor()
    parser.feed(html_content)
    headers = parser.headers

    issues = []
    recommendations = []

    # Check for single H1
    h1_count = sum(1 for h, _ in headers if h == "h1")
    if h1_count == 0:
        issues.append("Missing H1 tag")
        recommendations.append("Add a single H1 tag for the page title")
    elif h1_count > 1:
        issues.append(f"Multiple H1 tags found ({h1_count})")
        recommendations.append("Use only one H1 per page")

    # Check for skipped levels
    prev_level = 0
    for h, text in headers:
        level = int(h[1])
        if prev_level > 0 and level > prev_level + 1:
            issues.append(f"Skipped heading level: H{prev_level} to H{level}")
            recommendations.append(f"Don't skip from H{prev_level} to H{level}")
        prev_level = level

    # Check for empty headers
    for h, text in headers:
        if not text:
            issues.append(f"Empty {h.upper()} tag found")
            recommendations.append("All headers should have descriptive text")

    # Build hierarchy visualization
    hierarchy = []
    for h, text in headers:
        level = int(h[1])
        indent = "  " * (level - 1)
        hierarchy.append(f"{indent}{h.upper()}: {text[:50]}{'...' if len(text) > 50 else ''}")

    return {
        "headers": headers,
        "hierarchy": hierarchy,
        "h1_count": h1_count,
        "total_headers": len(headers),
        "issues": issues,
        "recommendations": recommendations,
        "score": max(0, 10 - len(issues) * 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze HTML header structure")
    parser.add_argument("input", nargs="?", help="HTML file to analyze (or stdin)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            html_content = f.read()
    else:
        html_content = sys.stdin.read()

    result = analyze_headers(html_content)

    if args.json:
        import json
        # Convert headers tuples to dicts for JSON
        result["headers"] = [{"tag": h, "text": t} for h, t in result["headers"]]
        print(json.dumps(result, indent=2))
    else:
        print("Header Structure Analysis")
        print("=" * 40)
        print(f"\nTotal headers: {result['total_headers']}")
        print(f"H1 count: {result['h1_count']}")
        print(f"Score: {result['score']}/10")

        print("\nHierarchy:")
        for line in result["hierarchy"]:
            print(f"  {line}")

        if result["issues"]:
            print("\nIssues Found:")
            for issue in result["issues"]:
                print(f"  - {issue}")

        if result["recommendations"]:
            print("\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  - {rec}")


if __name__ == "__main__":
    main()
