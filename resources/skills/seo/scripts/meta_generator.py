#!/usr/bin/env python3
"""Generate optimized meta tags for SEO."""

import argparse


def generate_meta_tags(
    title: str,
    description: str,
    url: str = "",
    image: str = "",
    site_name: str = "",
    twitter_handle: str = "",
    article_author: str = "",
    keywords: list[str] | None = None,
) -> str:
    """Generate HTML meta tags for SEO.

    Args:
        title: Page title (50-60 chars recommended)
        description: Meta description (150-160 chars recommended)
        url: Canonical URL
        image: OG image URL
        site_name: Site name for OG
        twitter_handle: Twitter @handle
        article_author: Author name
        keywords: Optional list of keywords

    Returns:
        HTML meta tags string
    """
    tags = []

    # Basic meta tags
    tags.append(f'<title>{title}</title>')
    tags.append(f'<meta name="description" content="{description}">')

    if keywords:
        tags.append(f'<meta name="keywords" content="{", ".join(keywords)}">')

    if article_author:
        tags.append(f'<meta name="author" content="{article_author}">')

    # Canonical URL
    if url:
        tags.append(f'<link rel="canonical" href="{url}">')

    # Open Graph tags
    tags.append("")
    tags.append("<!-- Open Graph -->")
    tags.append(f'<meta property="og:title" content="{title}">')
    tags.append(f'<meta property="og:description" content="{description}">')
    tags.append('<meta property="og:type" content="article">')

    if url:
        tags.append(f'<meta property="og:url" content="{url}">')
    if image:
        tags.append(f'<meta property="og:image" content="{image}">')
    if site_name:
        tags.append(f'<meta property="og:site_name" content="{site_name}">')

    # Twitter Card tags
    tags.append("")
    tags.append("<!-- Twitter Card -->")
    tags.append('<meta name="twitter:card" content="summary_large_image">')
    tags.append(f'<meta name="twitter:title" content="{title}">')
    tags.append(f'<meta name="twitter:description" content="{description}">')

    if image:
        tags.append(f'<meta name="twitter:image" content="{image}">')
    if twitter_handle:
        handle = twitter_handle if twitter_handle.startswith("@") else f"@{twitter_handle}"
        tags.append(f'<meta name="twitter:site" content="{handle}">')
        tags.append(f'<meta name="twitter:creator" content="{handle}">')

    return "\n".join(tags)


def validate_meta(title: str, description: str) -> list[str]:
    """Validate meta tag content and return warnings."""
    warnings = []

    if len(title) < 30:
        warnings.append(f"Title too short ({len(title)} chars). Aim for 50-60.")
    elif len(title) > 60:
        warnings.append(f"Title too long ({len(title)} chars). Keep under 60.")

    if len(description) < 120:
        warnings.append(f"Description too short ({len(description)} chars). Aim for 150-160.")
    elif len(description) > 160:
        warnings.append(f"Description too long ({len(description)} chars). Keep under 160.")

    return warnings


def main():
    parser = argparse.ArgumentParser(description="Generate SEO meta tags")
    parser.add_argument("--title", required=True, help="Page title")
    parser.add_argument("--description", required=True, help="Meta description")
    parser.add_argument("--url", help="Canonical URL")
    parser.add_argument("--image", help="OG image URL")
    parser.add_argument("--site-name", help="Site name")
    parser.add_argument("--twitter", help="Twitter handle")
    parser.add_argument("--author", help="Article author")
    parser.add_argument("--keywords", nargs="+", help="Keywords")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("--validate", action="store_true", help="Show validation warnings")

    args = parser.parse_args()

    if args.validate:
        warnings = validate_meta(args.title, args.description)
        if warnings:
            print("Warnings:")
            for w in warnings:
                print(f"  - {w}")
            print()

    tags = generate_meta_tags(
        title=args.title,
        description=args.description,
        url=args.url or "",
        image=args.image or "",
        site_name=args.site_name or "",
        twitter_handle=args.twitter or "",
        article_author=args.author or "",
        keywords=args.keywords,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(tags)
        print(f"Written to {args.output}")
    else:
        print(tags)


if __name__ == "__main__":
    main()
