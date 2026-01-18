#!/usr/bin/env python3
"""Analyze content for SEO factors."""

import argparse
import re
import sys
from html.parser import HTMLParser


class ContentExtractor(HTMLParser):
    """Extract text content from HTML."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_script = False
        self.in_style = False
        self.title = ""
        self.meta_description = ""
        self.links = {"internal": [], "external": []}
        self.images = []
        self.headers = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "script":
            self.in_script = True
        elif tag == "style":
            self.in_style = True
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            if attrs_dict.get("name", "").lower() == "description":
                self.meta_description = attrs_dict.get("content", "")
        elif tag == "a":
            href = attrs_dict.get("href", "")
            if href.startswith(("http://", "https://")):
                self.links["external"].append(href)
            elif href and not href.startswith(("#", "javascript:", "mailto:")):
                self.links["internal"].append(href)
        elif tag == "img":
            self.images.append({
                "src": attrs_dict.get("src", ""),
                "alt": attrs_dict.get("alt", ""),
            })
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.current_header = tag
            self.current_header_text = []

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
        elif tag == "style":
            self.in_style = False
        elif tag == "title":
            self.in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if hasattr(self, "current_header"):
                text = " ".join(self.current_header_text).strip()
                self.headers.append((self.current_header, text))
                del self.current_header

    def handle_data(self, data):
        if hasattr(self, "in_title") and self.in_title:
            self.title = data.strip()
        elif hasattr(self, "current_header"):
            self.current_header_text.append(data.strip())
        elif not self.in_script and not self.in_style:
            self.text_parts.append(data)

    def get_text(self):
        return " ".join(self.text_parts)


def analyze_content(content: str, is_html: bool = True, target_keyword: str = "") -> dict:
    """Analyze content for SEO factors.

    Args:
        content: Content to analyze (HTML or plain text)
        is_html: Whether content is HTML
        target_keyword: Optional target keyword to check for

    Returns:
        Analysis results dict
    """
    if is_html:
        parser = ContentExtractor()
        parser.feed(content)
        text = parser.get_text()
        title = parser.title
        meta_desc = parser.meta_description
        links = parser.links
        images = parser.images
        headers = parser.headers
    else:
        text = content
        title = ""
        meta_desc = ""
        links = {"internal": [], "external": []}
        images = []
        headers = []

    # Word count
    words = text.split()
    word_count = len(words)

    # Sentence count
    sentences = re.split(r"[.!?]+", text)
    sentence_count = len([s for s in sentences if s.strip()])

    # Average sentence length
    avg_sentence_length = word_count / max(sentence_count, 1)

    # Readability (simplified Flesch-Kincaid approximation)
    syllable_count = sum(max(1, len(re.findall(r"[aeiouy]+", w.lower()))) for w in words)
    readability_score = 206.835 - 1.015 * (word_count / max(sentence_count, 1)) - 84.6 * (syllable_count / max(word_count, 1))

    # Keyword analysis
    keyword_analysis = {}
    if target_keyword:
        keyword_lower = target_keyword.lower()
        text_lower = text.lower()
        keyword_count = text_lower.count(keyword_lower)
        keyword_density = (keyword_count * len(keyword_lower.split()) / max(word_count, 1)) * 100

        keyword_in_title = keyword_lower in title.lower() if title else False
        keyword_in_meta = keyword_lower in meta_desc.lower() if meta_desc else False
        keyword_in_h1 = any(keyword_lower in h[1].lower() for h in headers if h[0] == "h1")

        keyword_analysis = {
            "keyword": target_keyword,
            "count": keyword_count,
            "density": round(keyword_density, 2),
            "in_title": keyword_in_title,
            "in_meta_description": keyword_in_meta,
            "in_h1": keyword_in_h1,
        }

    # Image analysis
    images_without_alt = [img for img in images if not img.get("alt")]

    # Issues and recommendations
    issues = []
    recommendations = []

    if word_count < 300:
        issues.append(f"Content too short ({word_count} words)")
        recommendations.append("Aim for at least 300 words for better SEO")

    if title and len(title) > 60:
        issues.append(f"Title too long ({len(title)} chars)")
        recommendations.append("Keep title under 60 characters")

    if meta_desc and len(meta_desc) > 160:
        issues.append(f"Meta description too long ({len(meta_desc)} chars)")
        recommendations.append("Keep meta description under 160 characters")

    if images_without_alt:
        issues.append(f"{len(images_without_alt)} images missing alt text")
        recommendations.append("Add descriptive alt text to all images")

    if target_keyword and keyword_analysis.get("density", 0) < 0.5:
        issues.append(f"Low keyword density ({keyword_analysis['density']}%)")
        recommendations.append("Include target keyword more naturally in content")

    if target_keyword and not keyword_analysis.get("in_title"):
        issues.append("Target keyword not in title")
        recommendations.append("Include target keyword near the start of title")

    # Calculate score
    score = 10
    score -= len(issues) * 1.5
    score = max(0, min(10, score))

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "readability_score": round(readability_score, 1),
        "title": title,
        "title_length": len(title) if title else 0,
        "meta_description": meta_desc,
        "meta_description_length": len(meta_desc) if meta_desc else 0,
        "internal_links": len(links["internal"]),
        "external_links": len(links["external"]),
        "images": len(images),
        "images_without_alt": len(images_without_alt),
        "headers": [(h, t[:50]) for h, t in headers],
        "keyword_analysis": keyword_analysis,
        "issues": issues,
        "recommendations": recommendations,
        "score": round(score, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze content for SEO")
    parser.add_argument("input", nargs="?", help="File to analyze (or stdin)")
    parser.add_argument("--text", action="store_true", help="Input is plain text, not HTML")
    parser.add_argument("--keyword", help="Target keyword to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    result = analyze_content(content, is_html=not args.text, target_keyword=args.keyword or "")

    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print("Content Analysis")
        print("=" * 40)
        print(f"Score: {result['score']}/10")
        print(f"\nWord count: {result['word_count']}")
        print(f"Sentences: {result['sentence_count']}")
        print(f"Avg sentence length: {result['avg_sentence_length']} words")
        print(f"Readability: {result['readability_score']} (Flesch)")

        if result["title"]:
            print(f"\nTitle ({result['title_length']} chars): {result['title']}")
        if result["meta_description"]:
            print(f"Meta desc ({result['meta_description_length']} chars): {result['meta_description'][:60]}...")

        print(f"\nLinks: {result['internal_links']} internal, {result['external_links']} external")
        print(f"Images: {result['images']} total, {result['images_without_alt']} missing alt")

        if result["keyword_analysis"]:
            ka = result["keyword_analysis"]
            print(f"\nKeyword Analysis: '{ka['keyword']}'")
            print(f"  Count: {ka['count']}, Density: {ka['density']}%")
            print(f"  In title: {ka['in_title']}, In H1: {ka['in_h1']}")

        if result["issues"]:
            print("\nIssues:")
            for issue in result["issues"]:
                print(f"  - {issue}")

        if result["recommendations"]:
            print("\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  - {rec}")


if __name__ == "__main__":
    main()
