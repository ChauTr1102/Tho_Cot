"""
Extract product information from a TikTok Shop URL into structured JSON
(product_brief, brand_kit, audience_brief, market_signal, past_campaign_data)
using Agno + Gemini.

Usage:

    # Create a .env file in the same directory as agent.py:
    # GOOGLE_API_KEY="your-gemini-api-key"

    # Option 1 (default) - let Gemini read the URL with the url_context tool
    python agent.py "https://shop.tiktok.com/vn/pdp/..." -o output.json

    # Option 2 (recommended for TikTok Shop because the page uses JS rendering) -
    # render the page with Playwright before sending its content to Gemini
    pip install playwright && playwright install chromium
    python agent.py "https://shop.tiktok.com/vn/pdp/..." --render -o output.json

IMPORTANT TECHNICAL NOTE:
The Gemini API does not allow structured output (response_schema) and built-in
tools such as url_context in the same model call. If both are enabled, Gemini
silently ignores the schema and returns free-form text. This is not an error,
but Agno cannot parse it as an object, so .content is a str rather than a
TikTokShopExtraction. Therefore, "Option 1" uses two steps:
  Step 1: call Gemini with the url_context tool (without output_schema) to read
      and summarize the page as text.
  Step 2: call Gemini again without tools, with output_schema, and pass in the
      Step 1 text to force the correct JSON schema.
"Option 2" (--render) avoids this issue because it uses no tools: the page
content is passed directly in the prompt, so it can use a single model call.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
sys.path.append(".")
from pathlib import Path

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini

from app.services.extractor.schema import TikTokShopExtraction


EXTRACTION_RULES = [
    "IMPORTANT RULES:",
    "- ONLY fill in information clearly supported by the page content (product name, price, description, images, reviews, category, etc.).",
    "- NEVER invent figures. If a field is not present on the page (e.g. brand_colors, tone_of_voice, "
    "market_signal, past_campaign_data, required/restricted claims), leave it empty ([]), null, or an empty string "
    "as appropriate for its data type; do not over-infer.",
    "- Only fill 'required_claims' and 'restricted_or_forbidden_claims' when the page explicitly includes a warning, certification, "
    "or usage recommendation (e.g. 'dermatologically tested', 'do not use for children under 3'). "
    "Otherwise, leave the array empty; do not invent claims.",
    "- For 'brand_colors' and 'tone_of_voice', if the page has no clear brand guidelines, make a light inference "
    "from the dominant colors in the product/package images (if observable) and the product description style; if evidence is insufficient, "
    "leave the fields empty instead of guessing.",
    "- For 'product_photos' and 'existing_product_visuals', list product image URLs found on the page.",
    "- Set 'past_campaign_data.enabled' to false unless the page actually displays advertising campaign metrics "
    "(rare on a product page); this is optional data to be entered manually later.",
    "- Default 'audience_brief.platform' to 'TikTok Shop' unless other information is available.",
    "- Infer 3-6 reasonable search keywords for 'market_signal.search_keyword' from the product name and description.",
    "- Preserve the source language for descriptive fields when the source content is not English.",
]

# Instructions for the page-reading step (with tool, without schema)
READ_INSTRUCTIONS = [
    "You are a TikTok Shop product analyst working with a marketing team.",
    "Carefully read the TikTok Shop product page at the provided URL (use the url_context tool to retrieve its content).",
    "Then rewrite all observed information as a detailed, structured text summary, "
    "including the product name, category, description/USP, price, promotions, product image URLs, "
    "warnings/certifications/usage recommendations if present, notable reviews/comments if present, and any other details "
    "useful for creating a marketing brief.",
    "ONLY record information that is actually present on the page; do not infer or invent anything.",
    "This is NOT the JSON output step; it is a notes/summary step for the next stage.",
]

# Instructions for the schema-enforcement step (without tool, with output_schema)
STRUCTURE_INSTRUCTIONS = [
    "You have received a summary/notes about a TikTok Shop product.",
    "Task: convert that content into JSON matching the provided schema.",
] + EXTRACTION_RULES + [
    "Return ONLY JSON matching the provided schema, with no explanation.",
]

# Instructions for pre-rendered content (single step, without tool)
RENDER_INSTRUCTIONS = [
    "You are a TikTok Shop product analyst working with a marketing team.",
    "You are given pre-rendered text from a TikTok Shop product page (title, price, description, "
    "reviews, etc.) together with a list of image URLs found on the page. Extract the information into the JSON schema.",
] + EXTRACTION_RULES + [
    "Return ONLY JSON matching the provided schema, with no explanation.",
]


def _get_api_key() -> str:
    """Read the Gemini API key from environment or .env files."""
    load_dotenv()
    backend_env = Path(__file__).resolve().parents[3] / ".env"
    if backend_env.exists():
        load_dotenv(dotenv_path=backend_env)
    local_env = Path(__file__).resolve().parent / ".env"
    if local_env.exists():
        load_dotenv(dotenv_path=local_env)

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        raise ValueError(
            "Chưa cấu hình GOOGLE_API_KEY. Vui lòng thêm GOOGLE_API_KEY=\"AIza...\" vào file backend/.env hoặc biến môi trường."
        )
    return api_key.strip()


def _parse_result(content) -> TikTokShopExtraction:
    """Parse the structured response, with a fallback for string content."""
    if isinstance(content, TikTokShopExtraction):
        return content
    if isinstance(content, dict):
        if "error" in content:
            err = content["error"]
            err_msg = err.get("message") if isinstance(err, dict) else str(err)
            raise ValueError(f"Lỗi từ Gemini API: {err_msg}")
        return TikTokShopExtraction.model_validate(content)
    if isinstance(content, str):
        text = content.strip()
        if "No API key was provided" in text or "API_KEY_INVALID" in text:
            raise ValueError(
                "API Key Gemini không hợp lệ hoặc chưa được cung cấp. Vui lòng kiểm tra GOOGLE_API_KEY trong file backend/.env."
            )
        if text.startswith("{") and '"error"' in text:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict) and "error" in parsed:
                    err = parsed["error"]
                    err_msg = err.get("message") if isinstance(err, dict) else str(err)
                    raise ValueError(f"Lỗi từ Gemini API: {err_msg}")
            except json.JSONDecodeError:
                pass
        # Remove a code fence if the model wraps the JSON in ```json ... ```.
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return TikTokShopExtraction.model_validate_json(text)
    raise TypeError(f"Could not parse model result; unexpected content type: {type(content)}")


def run_with_url_context(url: str, model_id: str) -> TikTokShopExtraction:
    """Option 1: read the page, then convert the notes into schema-compliant JSON."""
    api_key = _get_api_key()
    candidate_models = [model_id]
    for fallback in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.6-pro", "gemini-2.0-flash"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error = None
    for cur_model in candidate_models:
        for attempt in range(3):
            try:
                # --- Step 1: read the page with the url_context tool ---
                reader_model = Gemini(
                    id=cur_model,
                    api_key=api_key,
                    url_context=True,
                    temperature=0.2,
                )
                reader_agent = Agent(model=reader_model, instructions=READ_INSTRUCTIONS, markdown=False)

                print(f"→ Step 1/2: Gemini ({cur_model}) is reading the page through url_context (attempt {attempt + 1})...", file=sys.stderr)
                read_response = reader_agent.run(
                    f"TikTok Shop product URL to analyze: {url}\n"
                    "Read this page and write a detailed summary according to the instructions."
                )
                page_notes = read_response.content
                if not isinstance(page_notes, str):
                    page_notes = str(page_notes)

                # --- Step 2: convert the notes to schema-compliant JSON ---
                structurer_model = Gemini(
                    id=cur_model,
                    api_key=api_key,
                    url_context=False,
                    temperature=0.1,
                )
                structurer_agent = Agent(
                    model=structurer_model,
                    instructions=STRUCTURE_INSTRUCTIONS,
                    output_schema=TikTokShopExtraction,
                    markdown=False,
                )

                print(f"→ Step 2/2: converting notes to schema-compliant JSON using {cur_model}...", file=sys.stderr)
                structured_response = structurer_agent.run(
                    f"Original product URL: {url}\n\nPage notes/summary:\n---\n{page_notes}\n---"
                )
                return _parse_result(structured_response.content)
            except Exception as e:
                err_str = str(e)
                last_error = e
                print(f"⚠️ Model {cur_model} (attempt {attempt + 1}) failed: {err_str}", file=sys.stderr)
                if any(k in err_str.lower() for k in ["503", "unavailable", "high demand", "429", "rate limit", "busy"]):
                    time.sleep(2)
                    continue
                if any(k in err_str.lower() for k in ["404", "not found", "no longer available", "validation error"]):
                    break
                break

    if last_error:
        raise last_error


def run_with_rendered_content(url: str, model_id: str) -> TikTokShopExtraction:
    """Option 2 (recommended): render with Playwright, then pass text and images in the prompt."""
    from app.services.extractor.render_tool import fetch_rendered_tiktok_shop

    print("→ Rendering the page with Playwright (headless Chromium)...", file=sys.stderr)
    page_data = fetch_rendered_tiktok_shop(url)

    if not page_data["text"].strip():
        print(
            "⚠️  Could not retrieve page content (it may be blocked or protected by a CAPTCHA). Try again later.",
            file=sys.stderr,
        )

    api_key = _get_api_key()
    prompt = (
        f"Original product URL: {url}\n\n"
        f"Page title: {page_data['title']}\n\n"
        f"Pre-rendered page text (title, price, description, reviews, specifications, etc.):\n"
        f"---\n{page_data['text'][:15000]}\n---\n\n"
        f"Image URLs found on the page (use for product_photos / existing_product_visuals):\n"
        f"{json.dumps(page_data['images'], ensure_ascii=False, indent=2)}\n\n"
        "Extract the information according to the provided schema."
    )

    candidate_models = [model_id]
    for fallback in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.6-pro", "gemini-2.0-flash"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error = None
    for cur_model in candidate_models:
        for attempt in range(3):
            try:
                print(f"→ Extracting schema-compliant JSON using model: {cur_model} (attempt {attempt + 1})...", file=sys.stderr)
                model = Gemini(id=cur_model, api_key=api_key, url_context=False, temperature=0.1)
                agent = Agent(
                    model=model,
                    instructions=RENDER_INSTRUCTIONS,
                    output_schema=TikTokShopExtraction,
                    markdown=False,
                )
                response = agent.run(prompt)
                return _parse_result(response.content)
            except Exception as e:
                err_str = str(e)
                last_error = e
                print(f"⚠️ Model {cur_model} (attempt {attempt + 1}) failed: {err_str}", file=sys.stderr)
                if any(k in err_str.lower() for k in ["503", "unavailable", "high demand", "429", "rate limit", "busy"]):
                    time.sleep(2)
                    continue
                if any(k in err_str.lower() for k in ["404", "not found", "no longer available", "validation error"]):
                    break
                break

    if last_error:
        raise last_error


def main():
    parser = argparse.ArgumentParser(description="Extract a marketing brief from a TikTok Shop URL using Gemini + Agno")
    parser.add_argument("url", help="TikTok Shop product URL")
    parser.add_argument("-o", "--output", default=None, help="Path to the JSON output file")
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render the page with Playwright before sending it to Gemini (recommended because TikTok Shop uses JS rendering)",
    )
    parser.add_argument(
        "--model",
        default="gemini-3.6-flash",
        help="Gemini model used for extraction (default: gemini-3.6-flash, the stable GA version when this script was written, "
        "08/2026). If this model has been deprecated, check the latest models at "
        "https://ai.google.dev/gemini-api/docs/models and pass it with --model.",
    )
    args = parser.parse_args()

    try:
        if args.render:
            result = run_with_rendered_content(args.url, args.model)
        else:
            result = run_with_url_context(args.url, args.model)
    except Exception as e:
        print(f"\n❌ Error calling the Gemini API: {e}", file=sys.stderr)
        print(
            "Suggestion: if the error is '404 NOT_FOUND ... model no longer available', Google has retired the model. "
            "Check the latest models at https://ai.google.dev/gemini-api/docs/models and retry with "
            "--model <new-model-id>.",
            file=sys.stderr,
        )
        sys.exit(1)

    output_dict = result.model_dump()
    pretty = json.dumps(output_dict, ensure_ascii=False, indent=2)
    print(pretty)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(pretty)
        print(f"\n✅ Saved the result to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()