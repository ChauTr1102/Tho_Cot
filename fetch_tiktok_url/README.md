# TikTok Shop → Marketing Brief Extractor (Agno + Gemini)

Extract `product_brief`, `brand_kit`, `audience_brief`, `market_signal`, and
`past_campaign_data` from a TikTok Shop URL into structured JSON using
[Agno](https://github.com/agno-agi/agno) as the agent framework and Gemini as the LLM.

## Installation

```bash
pip install -r requirements.txt

# If using --render mode (recommended; see below):
playwright install chromium
```

Get a Gemini API key at https://aistudio.google.com/apikey, then:

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

## Run

```bash
python agent.py "https://shop.tiktok.com/vn/pdp/julyhouse-xit-thom-quan-ao-huong-trai-cay-mua-he-280ml-100ml/1729673658154387468" -o output.json
```

The script defaults to `gemini-2.5-flash`, which is better suited than
`gemini-2.5-pro` for extraction because it is faster and cheaper. Choose another
model with `--model`, such as `--model gemini-2.5-flash-lite` to minimize cost.

## Two ways to retrieve page content

TikTok Shop renders content (price, images, description, etc.) with client-side
JavaScript, so the agent has two ways to read the page:

### Option 1 - default: Gemini `url_context` tool
Gemini has a built-in tool that fetches URL content on Google's servers
(`agno` maps directly to `Gemini(url_context=True)`). It is the simplest option
and requires no additional installation. The drawback is that Google's crawler
may **not see JS-rendered content**, or TikTok may block the bot, resulting in
incomplete data, especially prices, images, and reviews.

```bash
python agent.py "<url>" -o output.json
```

### Option 2 - recommended for TikTok Shop: `--render` (Playwright)
The script opens a headless Chromium browser, waits for the page to render,
collects all visible text and product image URLs, then sends that content to
Gemini instead of asking Gemini to fetch the page. This is much more reliable
for JS-heavy pages such as TikTok Shop.

```bash
pip install playwright
playwright install chromium
python agent.py "<url>" --render -o output.json
```

> Note: if the page has a CAPTCHA or blocks bots even in a real browser, you may
> need login cookies or a proxy. That is outside this script's scope, but
> `render_tool.py` can be extended with Playwright `storage_state` (cookies).

## File structure

- `schema.py` - Pydantic models describing the requested JSON schema. Agno uses
  this schema to make Gemini return structured output (`Agent(output_schema=...)`).
- `render_tool.py` - fallback Playwright tool for rendering JS pages before
  sending them to the LLM (used with `--render`).
- `agent.py` - main script: builds an Agno Agent with Gemini, runs extraction,
  and prints/saves the JSON result.

## Fields not available on the product page

Some schema fields (e.g. `brand_colors`, `tone_of_voice`, `market_signal`, and
`past_campaign_data`) usually **do not exist** on a standalone TikTok Shop
product page. They belong to internal brand guidelines or your historical
campaign data. The agent is instructed in `agent.py` **not to invent** these
fields. When no page evidence is found, it leaves them empty/null. Add these
sections manually or connect other sources, such as a brand guideline PDF or
Ads Manager report, if you want to automate them as well.

## Further extensions

- To have the LLM read multiple URLs in a batch, loop over the URL list and
  call `run_with_rendered_content()` or `run_with_url_context()` again.
- To connect real `past_campaign_data` from TikTok Ads Manager, add another
  tool that calls the TikTok Business API and passes the data into the prompt.
  The agent can then set `enabled: true` and populate the corresponding metrics.
