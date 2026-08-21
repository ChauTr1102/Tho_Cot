"""
generate_testcase_assets.py — one-off helper to populate a testcase folder's
brand_assets/ with REAL local files (brand logo + product photos) via
byteplus_ark.py (Seedream 5.0 Pro), so testcases/<name>/user_input.json can
reference local file paths instead of fake remote URLs.

This is NOT part of the QA_checklist.py runtime pipeline — it's a one-time
(or re-run-when-needed) content generator for the brand_kit section of a
testcase's user_input.json, which QA_checklist.py itself never generates
(brand_kit assets are supplied by the user in real usage, not by the
gen_plan/gen_assets agents). These files are meant to be committed (unlike
testcases/<name>/ark_out/, which is disposable per-run agent output).

Usage:
    cd QA_checklist
    python generate_testcase_assets.py bp01_fnb_sparkling_tea

Requires ARK_API_KEY (see .env.example). Costs real API calls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent
TESTCASES_DIR = REPO_ROOT / "testcases"

# Brand-kit image prompts per testcase. Add an entry here when adding a new
# testcase folder that needs generated brand_kit reference images.
BRAND_KIT_PROMPTS: dict[str, dict[str, str]] = {
    "bp01_fnb_sparkling_tea": {
        "brand_logo": (
            "minimalist e-commerce brand logo, text 'Fizzy Roots', deep teal #0E7C61 and "
            "warm yellow #F4D35E color palette, clean flat vector style, white background, "
            "no watermark"
        ),
        "product_photo_studio": (
            "a sparkling tea can labeled 'Fizzy Roots Hibiscus Ginger', studio product "
            "photography, front-facing, soft studio lighting, plain white background, "
            "brand colors deep teal #0E7C61 and warm yellow #F4D35E, no watermark"
        ),
        "product_photo_lifestyle": (
            "a sparkling tea can labeled 'Fizzy Roots Hibiscus Ginger' held at a beach "
            "setting, natural daylight, lifestyle product photography, brand colors deep "
            "teal #0E7C61 and warm yellow #F4D35E, no watermark"
        ),
    },
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in BRAND_KIT_PROMPTS:
        print(f"Usage: python generate_testcase_assets.py <{'|'.join(BRAND_KIT_PROMPTS)}>")
        return 1

    testcase_name = sys.argv[1]
    testcase_dir = TESTCASES_DIR / testcase_name
    out_dir = testcase_dir / "brand_assets"
    out_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(REPO_ROOT))
    import byteplus_ark as ark  # imported lazily so this script fails fast with a clear
                                 # message if ARK_API_KEY is missing, without breaking
                                 # QA_checklist.py's own lazy-import pattern.

    prompts = BRAND_KIT_PROMPTS[testcase_name]
    generated: dict[str, str] = {}

    for name, prompt in prompts.items():
        print(f"Generating '{name}' via Seedream 5.0 Pro...")
        url = ark.text_to_image(prompt, size="1024x1024")
        # Download directly into the testcase's own ark_out/, not byteplus_ark's
        # shared OUT dir, by writing the bytes ourselves.
        import requests
        dest = out_dir / f"{name}.jpg"
        with requests.get(url, stream=True, timeout=180) as r:
            r.raise_for_status()
            dest.write_bytes(r.content)
        generated[name] = str(dest.resolve())
        print(f"  -> saved: {dest}")

    print("\nGenerated files:")
    print(json.dumps(generated, indent=2, ensure_ascii=False))
    print(
        "\nUpdate this testcase's user_input.json brand_kit fields to point at these "
        "local paths (e.g. brand_kit.logo_url -> './brand_assets/brand_logo.jpg', "
        "brand_kit.product_photo_urls -> ['./brand_assets/product_photo_studio.jpg', "
        "'./brand_assets/product_photo_lifestyle.jpg'])."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
