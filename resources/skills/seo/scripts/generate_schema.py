#!/usr/bin/env python3
"""Generate JSON-LD structured data for various schema types."""

import argparse
import json
from datetime import datetime


def generate_article_schema(
    headline: str,
    author_name: str,
    date_published: str,
    description: str = "",
    author_url: str = "",
    publisher_name: str = "",
    publisher_logo: str = "",
    image: str = "",
    date_modified: str = "",
) -> dict:
    """Generate Article schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "author": {"@type": "Person", "name": author_name},
        "datePublished": date_published,
    }

    if description:
        schema["description"] = description
    if author_url:
        schema["author"]["url"] = author_url
    if date_modified:
        schema["dateModified"] = date_modified
    if image:
        schema["image"] = image
    if publisher_name:
        schema["publisher"] = {"@type": "Organization", "name": publisher_name}
        if publisher_logo:
            schema["publisher"]["logo"] = {"@type": "ImageObject", "url": publisher_logo}

    return schema


def generate_faq_schema(questions: list[tuple[str, str]]) -> dict:
    """Generate FAQPage schema.

    Args:
        questions: List of (question, answer) tuples
    """
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in questions
        ],
    }


def generate_product_schema(
    name: str,
    description: str,
    brand: str = "",
    price: str = "",
    currency: str = "USD",
    availability: str = "InStock",
    rating: float = 0,
    review_count: int = 0,
) -> dict:
    """Generate Product schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "description": description,
    }

    if brand:
        schema["brand"] = {"@type": "Brand", "name": brand}
    if price:
        schema["offers"] = {
            "@type": "Offer",
            "price": price,
            "priceCurrency": currency,
            "availability": f"https://schema.org/{availability}",
        }
    if rating and review_count:
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(rating),
            "reviewCount": str(review_count),
        }

    return schema


def generate_howto_schema(name: str, description: str, steps: list[tuple[str, str]]) -> dict:
    """Generate HowTo schema.

    Args:
        name: Title of the how-to
        description: Brief description
        steps: List of (step_name, step_text) tuples
    """
    return {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": name,
        "description": description,
        "step": [
            {"@type": "HowToStep", "name": name, "text": text}
            for name, text in steps
        ],
    }


def generate_organization_schema(
    name: str,
    url: str,
    logo: str = "",
    same_as: list[str] | None = None,
    telephone: str = "",
) -> dict:
    """Generate Organization schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name,
        "url": url,
    }

    if logo:
        schema["logo"] = logo
    if same_as:
        schema["sameAs"] = same_as
    if telephone:
        schema["contactPoint"] = {
            "@type": "ContactPoint",
            "telephone": telephone,
            "contactType": "customer service",
        }

    return schema


SCHEMA_TYPES = {
    "article": generate_article_schema,
    "faq": generate_faq_schema,
    "product": generate_product_schema,
    "howto": generate_howto_schema,
    "organization": generate_organization_schema,
}


def main():
    parser = argparse.ArgumentParser(description="Generate JSON-LD structured data")
    parser.add_argument("type", choices=SCHEMA_TYPES.keys(), help="Schema type")
    parser.add_argument("--json-input", help="JSON file with schema data")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")

    args = parser.parse_args()

    if args.json_input:
        with open(args.json_input) as f:
            data = json.load(f)

        if args.type == "faq" and "questions" in data:
            data["questions"] = [(q["question"], q["answer"]) for q in data["questions"]]
        if args.type == "howto" and "steps" in data:
            data["steps"] = [(s["name"], s["text"]) for s in data["steps"]]

        schema = SCHEMA_TYPES[args.type](**data)
    else:
        print(f"Error: --json-input required for {args.type} schema")
        print("Create a JSON file with the required fields.")
        return 1

    indent = 2 if args.pretty else None
    output = json.dumps(schema, indent=indent)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
