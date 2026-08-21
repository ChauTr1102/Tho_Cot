"""
The director: an LLM decides what this campaign needs and how to build it.

Until now the graph was fixed — the same seven slots and four shots for every
brand, whatever the plan said. That is a content generator with extra steps. A
campaign for a 9.9 flash sale and a campaign for a bean-to-bar gift box want
different assets, different aspect ratios, different numbers of shots, and very
different art direction, and deciding that is the part BP-01 actually asks for:
*"can we decide what to say, who to say it to, what assets to create."*

So the director runs twice per campaign:

    draft(plan, input)   -> a short, readable proposal a human approves
    design(draft, ...)   -> the node graph that produces it

Both are LLM calls that return JSON. Neither is trusted.

**The vocabulary is closed.** The model chooses how many nodes there are, what
each one is for, how they connect and what prompt each carries — but every node
must be one of the kinds in `NODE_KINDS`, because those are the ones that map to
code that exists. A model inventing a `magic_upscale` node produces a graph that
cannot run, and it will invent one if allowed to. Freedom over structure,
constraint over vocabulary.

Everything the model returns is then validated and repaired: unknown kinds are
dropped, unknown dependencies are cut, cycles are broken, and a graph with no
runnable node falls back to the deterministic layout in `pipeline.build_nodes`.
A demo that renders a slightly duller campaign is survivable; one that raises a
KeyError in front of judges is not.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.schemas.studio import CampaignInput, CampaignPlan, Platform
from app.services.studio import ark, wording

# The closed vocabulary. Each maps to a node builder in `pipeline`.
NODE_KINDS: dict[str, str] = {
    "inventory": "Triage the brand's existing photographs. No prompt. At most one.",
    "hero": "One art-directed image of the product that every later image uses as "
            "its style reference. No on-screen text. At most one, and everything "
            "generated should depend on it.",
    "image": "A marketplace still: listing image, SKU close-up, collection, banner, cover.",
    "poster": "A sale poster: flat vivid background, huge display headline, discount "
              "badges, a call-to-action button, contact line. Text-heavy by design.",
    "keyframe": "The first frame of one video shot. Carries that shot's on-screen text.",
    "clip": "Animates one keyframe into a 5-second clip. Must depend on exactly one keyframe.",
    "voiceover": "Vietnamese narration for the whole video. Depends on nothing but the brief.",
    "assemble": "Joins clips into the master video, adds voiceover and subtitles, cuts "
                "shorter versions. Depends on every clip it joins.",
}

RATIOS = ("1:1", "9:16", "4:5", "2:1")


@dataclass
class Deliverable:
    """One thing the campaign will produce, in words a human can approve."""
    id: str
    kind: str
    platform: str
    ratio: str
    purpose: str = ""


@dataclass
class Register:
    """The campaign's visual register, written by the director rather than chosen.

    The look library in `looks.py` holds six presets, and for a while the
    director picked one. That was the wrong shape: a brief can want cute, or
    cinematic, or deliberately plain for an office-worker audience, or a loud
    9.9 sale, and those are not six cases — they are however many the market
    has. A closed list turns every campaign into the nearest preset.

    So the register is authored per campaign, in the same five fields a preset
    uses, and then applied *uniformly* to every prompt in the run. Freedom in
    choosing the look; discipline in applying it. That uniformity is what makes
    eight images read as one shoot, and it does not care whether the wording
    came from a preset or from the model.

    `source` records where it came from, because a director that quietly fell
    back to a preset should be visible.
    """
    name: str = ""
    lens: str = ""
    light: str = ""
    surface: str = ""
    grade: str = ""
    palette: list[str] = field(default_factory=list)
    why: str = ""
    source: str = "director"       # director | preset | fallback

    def as_spine(self):
        """Adapt to the `StyleSpine` the prompt assembler already takes."""
        from app.services.studio.direct import StyleSpine
        return StyleSpine(
            look_key=self.name or "director",
            lens=self.lens, light=self.light, surface=self.surface,
            grade=self.grade, palette=list(self.palette),
        )


@dataclass
class Draft:
    """The proposal shown before anything is rendered."""
    summary: str = ""
    register: Register = field(default_factory=Register)
    platforms: list[str] = field(default_factory=list)
    deliverables: list[Deliverable] = field(default_factory=list)
    video_shots: int = 4
    video_seconds: int = 20
    notes: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeSpec:
    """One node of an LLM-designed graph, after validation."""
    id: str
    kind: str
    deps: list[str] = field(default_factory=list)
    ratio: str = "1:1"
    platform: str = "shopee"
    prompt: str = ""
    texts: list[tuple[str, str]] = field(default_factory=list)
    role: str = ""
    seconds: int = 5
    #: Which creative route this node argues for. Empty for everything the two
    #: routes share — the product photograph does not have an opinion.
    route: str = ""


@dataclass
class GraphSpec:
    nodes: list[NodeSpec] = field(default_factory=list)
    rationale: str = ""
    repaired: list[str] = field(default_factory=list)

    @property
    def is_runnable(self) -> bool:
        """A graph is worth running if it produces at least one visible asset."""
        return any(n.kind in {"image", "poster", "keyframe", "clip"} for n in self.nodes)


# ---------------------------------------------------------------------------
# Step one: the draft
# ---------------------------------------------------------------------------

_DRAFT_SYSTEM = (
    "Bạn là giám đốc chiến dịch thương mại điện tử tại Đông Nam Á. "
    "Bạn quyết định một chiến dịch cần những asset nào, cho sàn nào, và vì sao. "
    "Trả lời DUY NHẤT bằng một JSON object, không giải thích thêm."
)


def _brief_digest(plan: CampaignPlan, campaign_input: CampaignInput | None,
                  research: str = "") -> str:
    """The compact brief the director reasons over.

    Deliberately short. A model handed the whole plan spends its attention
    summarising rather than deciding — which is why `research` is an excerpt and
    not the sixteen thousand characters the research stage actually wrote.

    What earns a line here is what can change the *look*. The benefit hierarchy
    says which promise the frame should lead with; the competitor angle says
    what it must not look like; the trend and the search keywords say what a
    shopper is already scrolling past. All four were being produced upstream,
    carried through the adapter, and then not shown to the one component whose
    whole job is to decide how the campaign should look.
    """
    lines = [f"Sản phẩm: {campaign_input.product_brief.product_name if campaign_input else ''}"]
    if campaign_input:
        b, a, m = campaign_input.product_brief, campaign_input.audience_brief, campaign_input.market_signal
        lines += [
            f"Ngành hàng: {b.category}",
            f"Điểm bán: {'; '.join(b.key_selling_points[:4])}",
            f"Giá/khuyến mãi: {b.price_or_promotion or 'không có'}",
            f"Thị trường: {b.target_market}",
            f"Khách hàng: {a.target_customer}",
            f"Sàn gợi ý: {', '.join(a.platform) or 'chưa rõ'}",
            f"Dịp: {m.seasonal_moment or 'không có'}",
            f"Nỗi đau: {m.consumer_pain_point or 'không có'}",
            f"Mục tiêu: {m.campaign_objective or 'không có'}",
            f"Xu hướng: {m.trend or 'không có'}",
            f"Đối thủ đang làm: {m.competitor_angle or 'không có'}",
            f"Từ khoá tìm kiếm: {m.search_keyword or 'không có'}",
            f"Tông thương hiệu: {campaign_input.brand_kit.tone_of_voice or 'không có'}",
            f"CLAIM CẤM: {'; '.join(b.forbidden_claims) or 'không có'}",
        ]
    # Upstream writes its own field names into its values — "Góc chiến dịch
    # chính: …" — so labelling them again gives the director "Góc chiến dịch:
    # Góc chiến dịch chính: …". It is only tokens, but it is also the string
    # that ends up quoted onto artwork if anything downstream trusts it.
    lines += [
        f"Góc chiến dịch: {wording.strip_label(plan.positioning.main_campaign_angle)}",
        f"Khách mục tiêu: {wording.strip_label(plan.positioning.target_audience)}",
        f"Thông điệp: {wording.strip_label(plan.positioning.key_selling_message)}",
    ]
    if plan.positioning.product_benefit_hierarchy:
        # Ranked upstream, and the rank is the point: it says which promise the
        # frame leads with and which two are supporting detail.
        ranked = plan.positioning.product_benefit_hierarchy[:3]
        lines.append("Lợi ích theo thứ tự: "
                     + " > ".join(wording.shorten(b, 70) for b in ranked))
    for r in plan.creative_routes[:2]:
        lines.append(f"Route {r.route_id}: {r.hook_idea} | {r.visual_direction}")
    if research.strip():
        lines.append("Trích nghiên cứu thị trường:\n" + research.strip())
    return "\n".join(l for l in lines if l.strip())


def draft(plan: CampaignPlan, campaign_input: CampaignInput | None = None,
          direction: str = "", research: str = "") -> Draft:
    """Ask the director what this campaign should produce.

    `direction` is whatever the user typed — "dễ thương", "điện ảnh", "cho dân
    văn phòng", "sale tưng bừng 9.9", or nothing at all. It outranks the
    director's own reading of the brief, because the person asking knows
    something the brief does not say.

    Falls back to a sensible fixed proposal if the model is unreachable or
    answers with something unusable — the run must still be startable.
    """
    steer = (f"\n\nNGƯỜI DÙNG YÊU CẦU (ưu tiên cao nhất, đè lên suy luận của bạn): "
             f"{direction.strip()}" if direction.strip() else "")
    prompt = f"""{_brief_digest(plan, campaign_input, research)}{steer}

Đề xuất bộ asset cho chiến dịch này. Cân nhắc:
- Sàn nào đáng làm. TikTok Shop là video-first, người xem đang lướt. Shopee là
  ảnh-first, người mua đang so sánh trước khi trả tiền.
- Dịp khuyến mãi mạnh thì cần poster sale chữ to, badge giảm giá, nút mua ngay.
  Sản phẩm cao cấp kể chuyện thì cần ảnh editorial, ít chữ.
- Ảnh chính của Shopee bắt buộc nền trắng thuần.

Cũng quyết định LUÔN "register" — ngôn ngữ hình của chiến dịch này. Đừng chọn
trong một danh sách có sẵn: hãy viết ra nó. Có chiến dịch cần tưng bừng sale
chữ to badge đỏ, có chiến dịch cần dễ thương pastel, có chiến dịch cần điện ảnh
tối giản, có chiến dịch nói với dân văn phòng nên phải điềm đạm. Viết như một
chỉ đạo cho nhiếp ảnh gia: bố trí đèn cụ thể, bề mặt cụ thể, ống kính và khẩu độ,
cách grade màu — không phải tính từ chung chung.

Trả về JSON đúng dạng:
{{
  "summary": "2-3 câu tiếng Việt: chiến dịch này sẽ làm gì và vì sao",
  "register": {{
    "name": "tên ngắn không dấu, ví dụ flash_sale_do hoặc cute_pastel",
    "lens": "tiêu cự và khẩu độ, ví dụ 85mm at f/8",
    "light": "BỐ TRÍ ĐÈN cụ thể, không phải thời tiết",
    "surface": "cái SET cụ thể, không phải một danh từ",
    "grade": "cách grade màu",
    "palette": ["#RRGGBB", "..."],
    "why": "một câu tiếng Việt vì sao register này hợp brief"
  }},
  "platforms": ["tiktok_shop" và/hoặc "shopee"],
  "deliverables": [
    {{"id": "shopee_main", "kind": "image|poster", "platform": "shopee",
      "ratio": "1:1|9:16|4:5|2:1", "purpose": "một câu tiếng Việt"}}
  ],
  "video_shots": 3-5,
  "video_seconds": 15-30,
  "notes": ["điều đáng lưu ý khi dựng, tiếng Việt"]
}}

Từ 4 đến 8 deliverable. Dùng đúng hai giá trị platform và bốn giá trị ratio ở trên."""

    try:
        raw = ark.parse_json(ark.chat(prompt, system=_DRAFT_SYSTEM, json_mode=True))
    except Exception:
        return _fallback_draft(plan, campaign_input)
    if not isinstance(raw, dict):
        return _fallback_draft(plan, campaign_input)

    platforms = [p for p in raw.get("platforms", []) if p in {x.value for x in Platform}]
    deliverables = []
    for item in raw.get("deliverables", []):
        if not isinstance(item, dict) or not item.get("id"):
            continue
        kind = item.get("kind", "image")
        deliverables.append(Deliverable(
            id=str(item["id"])[:40],
            kind=kind if kind in {"image", "poster"} else "image",
            platform=item.get("platform") if item.get("platform") in {x.value for x in Platform}
                     else (platforms[0] if platforms else "shopee"),
            ratio=item.get("ratio") if item.get("ratio") in RATIOS else "1:1",
            purpose=str(item.get("purpose", ""))[:200],
        ))

    if not deliverables:
        return _fallback_draft(plan, campaign_input)

    return Draft(
        summary=str(raw.get("summary", ""))[:600],
        register=_register_from(raw.get("register"), campaign_input),
        platforms=platforms or ["shopee"],
        deliverables=deliverables,
        video_shots=_clamp(raw.get("video_shots", 4), 2, 6),
        video_seconds=_clamp(raw.get("video_seconds", 20), 10, 30),
        notes=[str(n)[:200] for n in raw.get("notes", [])][:5],
        raw=raw,
    )


def _register_from(raw: Any, campaign_input: CampaignInput | None) -> Register:
    """Read the director's register, or borrow the nearest preset if it is thin.

    A register with an empty `light` or `surface` is worse than a preset: those
    two fields carry most of what makes an image look directed rather than
    snapshot. So a half-answer is discarded in favour of `looks.pick_looks`,
    which at least gives a complete, coherent direction.
    """
    if isinstance(raw, dict):
        reg = Register(
            name=str(raw.get("name", "")).strip()[:40],
            lens=str(raw.get("lens", "")).strip()[:160],
            light=str(raw.get("light", "")).strip()[:300],
            surface=str(raw.get("surface", "")).strip()[:300],
            grade=str(raw.get("grade", "")).strip()[:200],
            palette=[str(c)[:16] for c in raw.get("palette", []) if str(c).strip()][:6],
            why=str(raw.get("why", "")).strip()[:200],
            source="director",
        )
        if reg.light and reg.surface and reg.lens:
            if not reg.palette and campaign_input:
                reg.palette = list(campaign_input.brand_kit.brand_colors)[:4]
            return reg

    from app.services.studio.looks import LOOKS, pick_looks
    brief = campaign_input.product_brief if campaign_input else None
    key = pick_looks(brief.category if brief else "",
                     campaign_input.brand_kit.tone_of_voice or "" if campaign_input else "",
                     campaign_input.market_signal.trend or "" if campaign_input else "")[0]
    look = LOOKS[key]
    return Register(
        name=key, lens=look.lens, light=look.light, surface=look.surface,
        grade=look.grade,
        palette=list(campaign_input.brand_kit.brand_colors)[:4] if campaign_input else [],
        why="Director không đưa register đủ dùng — lấy preset gần nhất.",
        source="preset",
    )


def _clamp(value: Any, low: int, high: int) -> int:
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return low


def _fallback_draft(plan: CampaignPlan, campaign_input: CampaignInput | None) -> Draft:
    """The proposal used when the director cannot be reached.

    Not a placeholder: this is the deterministic kit the studio shipped before
    the director existed, so a failed LLM call costs variety, not the run.
    """
    platforms = list(campaign_input.audience_brief.platform) if campaign_input else []
    platforms = [p for p in platforms if p in {x.value for x in Platform}] or ["shopee"]
    promo = bool(campaign_input and campaign_input.product_brief.price_or_promotion)
    items = [
        Deliverable("shopee_main", "image", "shopee", "1:1", "Ảnh chính, nền trắng theo luật sàn"),
        Deliverable("shopee_sku", "image", "shopee", "1:1", "Cận nhãn để người mua soi"),
        Deliverable("shopee_collection", "image", "shopee", "1:1", "Bày combo"),
    ]
    if promo:
        items.append(Deliverable("shopee_banner", "poster", "shopee", "2:1", "Poster khuyến mãi"))
    if "tiktok_shop" in platforms:
        items.append(Deliverable("tiktok_cover", "image", "tiktok_shop", "9:16", "Ảnh bìa video"))
    return Draft(
        summary=plan.positioning.main_campaign_angle or "Bộ asset mặc định.",
        platforms=platforms, deliverables=items,
        notes=["Director không phản hồi — dùng bộ kit mặc định."],
    )


# ---------------------------------------------------------------------------
# Step two: the graph
# ---------------------------------------------------------------------------

_DESIGN_SYSTEM = (
    "Bạn thiết kế đồ thị thực thi cho một studio sinh ảnh và video quảng cáo. "
    "Trả lời DUY NHẤT bằng một JSON object."
)


def design(draft_: Draft, plan: CampaignPlan,
           campaign_input: CampaignInput | None = None,
           with_video: bool = True) -> GraphSpec:
    """Turn an approved draft into a node graph, and validate whatever comes back."""
    reg = draft_.register
    register_block = (
        f"REGISTER của chiến dịch (áp dụng NGUYÊN VĂN vào mọi prompt, không đổi chữ):\n"
        f"  lens: {reg.lens}\n  light: {reg.light}\n  surface: {reg.surface}\n"
        f"  grade: {reg.grade}\n  palette: {', '.join(reg.palette) or 'màu của sản phẩm'}\n"
        f"  (vì sao: {reg.why})\n"
    ) if reg.light else ""
    vocabulary = "\n".join(f'  "{k}": {v}' for k, v in NODE_KINDS.items())
    wanted = "\n".join(
        f'  - {d.id}: {d.kind}, {d.platform}, {d.ratio} — {d.purpose}'
        for d in draft_.deliverables
    )
    forbidden = "; ".join(campaign_input.product_brief.forbidden_claims) if campaign_input else ""
    label = ", ".join(f'"{s}"' for s in _label_strings(campaign_input))

    prompt = f"""{_brief_digest(plan, campaign_input)}

{register_block}
Bộ asset đã duyệt:
{wanted}
{"Video: " + str(draft_.video_shots) + " shot, tổng " + str(draft_.video_seconds) + " giây." if with_video else "Lần này KHÔNG làm video."}

Các loại node được phép (không được bịa loại khác):
{vocabulary}

Thiết kế đồ thị. Quy tắc bắt buộc:
- Có đúng một node "inventory" không phụ thuộc gì, và đúng một node "hero" phụ thuộc inventory.
- Mọi node "image" và "poster" phụ thuộc "hero" (để cả bộ cùng một gu ánh sáng).
- Mỗi "clip" phụ thuộc đúng một "keyframe".
- "assemble" phụ thuộc tất cả "clip" và cả "voiceover" nếu có.
- Chữ nào sẽ hiện trên ảnh thì phải ghi rõ trong "texts". Đừng để model đoán.
- Mọi prompt phải mang NGUYÊN VĂN register ở trên: cùng lens, cùng light, cùng
  surface, cùng grade. Chỉ đổi bố cục và nội dung từng khung. Sự lặp lại đó
  chính là thứ khiến cả bộ trông như một buổi chụp.
- TUYỆT ĐỐI KHÔNG dùng các claim này ở bất kỳ đâu: {forbidden or "(không có)"}
- Nhãn in trên bao bì sản phẩm là: {label or "(không rõ)"}

Trả về JSON:
{{
  "rationale": "2-3 câu tiếng Việt giải thích vì sao đồ thị này",
  "nodes": [
    {{"id": "hero", "kind": "hero", "deps": ["inventory"], "ratio": "1:1",
      "platform": "shopee", "prompt": "mô tả cảnh bằng tiếng Anh, chi tiết ánh sáng và bố cục",
      "texts": [], "role": "", "seconds": 5}}
  ]
}}

"texts" là danh sách cặp [vai_trò, chuỗi_chữ], ví dụ [["headline","BẤT NGỜ TUNG DEAL"],["badge","GIẢM 50%"]].
Chữ trên ảnh viết bằng tiếng Việt. "prompt" viết bằng tiếng Anh."""

    try:
        raw = ark.parse_json(ark.chat(prompt, system=_DESIGN_SYSTEM,
                                      json_mode=True, max_tokens=2600,
                                      timeout=420))
    except Exception as exc:
        return GraphSpec(rationale="", repaired=[f"director không phản hồi: {exc}"])
    if not isinstance(raw, dict):
        return GraphSpec(repaired=["director trả về thứ không phải JSON object"])

    return _validate(raw, forbidden_claims=(campaign_input.product_brief.forbidden_claims
                                            if campaign_input else []))


def _label_strings(campaign_input: CampaignInput | None) -> list[str]:
    if not campaign_input:
        return []
    name = campaign_input.product_brief.product_name
    return [w for w in [name] if w][:4]


def _validate(raw: dict[str, Any], forbidden_claims: list[str]) -> GraphSpec:
    """Repair an LLM-designed graph into one that can actually run.

    Every rule here corresponds to a way a model has been observed to produce
    something plausible-looking and unrunnable. Repairs are recorded rather than
    silent: a director whose graph needed six fixes is worth knowing about.
    """
    repaired: list[str] = []
    nodes: list[NodeSpec] = []
    seen: set[str] = set()
    banned = [c.casefold() for c in forbidden_claims if c.strip()]

    for item in raw.get("nodes", []):
        if not isinstance(item, dict):
            continue
        node_id = str(item.get("id", "")).strip()[:48]
        kind = str(item.get("kind", "")).strip()
        if not node_id or kind not in NODE_KINDS:
            repaired.append(f"bỏ node không hợp lệ: {item.get('id') or item.get('kind')}")
            continue
        if node_id in seen:
            repaired.append(f"bỏ node trùng id: {node_id}")
            continue
        seen.add(node_id)

        texts: list[tuple[str, str]] = []
        for pair in item.get("texts", []):
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                role, value = str(pair[0])[:24], str(pair[1])[:120]
            elif isinstance(pair, dict):
                role, value = str(pair.get("role", "text"))[:24], str(pair.get("value", ""))[:120]
            else:
                continue
            if not value.strip():
                continue
            # A claim that cannot be written cannot be drawn either.
            if any(b in value.casefold() for b in banned):
                repaired.append(f"{node_id}: bỏ chữ chứa claim cấm — {value[:40]}")
                continue
            texts.append((role, value))

        nodes.append(NodeSpec(
            id=node_id, kind=kind,
            deps=[str(d)[:48] for d in item.get("deps", []) if str(d).strip()],
            ratio=item.get("ratio") if item.get("ratio") in RATIOS else "1:1",
            platform=item.get("platform") if item.get("platform") in {p.value for p in Platform}
                     else "shopee",
            prompt=str(item.get("prompt", ""))[:2000],
            texts=texts,
            role=str(item.get("role", ""))[:24],
            seconds=_clamp(item.get("seconds", 5), 4, 15),
        ))

    ids = {n.id for n in nodes}

    # Cut edges to nodes that do not exist, and self-edges.
    for node in nodes:
        kept = [d for d in node.deps if d in ids and d != node.id]
        if len(kept) != len(node.deps):
            repaired.append(f"{node.id}: cắt cạnh trỏ tới node không tồn tại")
        node.deps = kept

    # Break cycles by dropping the edge that closes one. Depth-first, iterative,
    # because a model asked for a DAG will occasionally hand back a ring.
    order: dict[str, int] = {}
    def _rank(node_id: str, stack: set[str]) -> int:
        if node_id in order:
            return order[node_id]
        node = next(n for n in nodes if n.id == node_id)
        stack.add(node_id)
        best = 0
        for dep in list(node.deps):
            if dep in stack:
                node.deps.remove(dep)
                repaired.append(f"{node.id}: phá vòng lặp, bỏ cạnh -> {dep}")
                continue
            best = max(best, _rank(dep, stack) + 1)
        stack.discard(node_id)
        order[node_id] = best
        return best

    for node in list(nodes):
        _rank(node.id, set())

    # Structural repairs the executor would otherwise choke on.
    for node in nodes:
        if node.kind == "clip":
            keyframes = [d for d in node.deps
                         if any(n.id == d and n.kind == "keyframe" for n in nodes)]
            if len(keyframes) != 1:
                repaired.append(f"{node.id}: clip phải phụ thuộc đúng một keyframe")
            node.deps = keyframes[:1] or node.deps[:1]

    return GraphSpec(nodes=nodes, rationale=str(raw.get("rationale", ""))[:600],
                     repaired=repaired)


def plan_graph(draft_: Draft, plan: CampaignPlan,
               campaign_input: CampaignInput | None = None,
               with_video: bool = True) -> GraphSpec:
    """Derive the graph from an approved draft, in code.

    An earlier version asked the LLM to design the graph too. It worked and it
    was too slow to demo: the model bills by output length, not by difficulty,
    and a graph with a written prompt per node is thousands of tokens — measured
    at 165 seconds, and 101 even after the output was trimmed. It also produced
    graphs that had to be repaired: two `hero` nodes in one answer, and a hero
    staged around a person, which Seedance then refuses as a video reference.

    So the division moved. The director still decides everything that needs
    judgement — which platforms, which deliverables, how many shots, and the
    register, all shaped by what the user asked for. The wiring is arithmetic:
    stills depend on the hero, each clip on its keyframe, the master on every
    clip. There is no creativity in that, and paying three minutes for a model
    to rediscover it is a bad trade in front of an audience.

    Scene text still comes from the director — it is carried on each
    `Deliverable.purpose` — so the frames differ per campaign. Only the edges
    are fixed.
    """
    nodes: list[NodeSpec] = []
    texts = _campaign_texts(plan, campaign_input)
    label = _label_strings(campaign_input)
    platform = (draft_.platforms or ["shopee"])[0]

    nodes.append(NodeSpec(id="inventory", kind="inventory", deps=[], platform=platform))
    nodes.append(NodeSpec(id="hero", kind="hero", deps=["inventory"],
                          ratio="1:1", platform=platform,
                          prompt="the product centred, lit exactly as the register describes"))

    for item in draft_.deliverables:
        is_poster = item.kind == "poster"
        # A poster carries the campaign's whole message; a still carries at most
        # a headline. Handing every string to every frame is how a listing image
        # ends up looking like a leaflet.
        node_texts = list(texts) if is_poster else [t for t in texts if t[0] == "headline"]
        if item.id.endswith("main") or "main" in item.id:
            node_texts = []          # the marketplace listing image stays clean
        nodes.append(NodeSpec(
            id=item.id, kind=item.kind, deps=["hero"],
            ratio=item.ratio, platform=item.platform,
            prompt=item.purpose or "the product, staged for this slot",
            texts=node_texts,
        ))

    # ── The A/B pair ──────────────────────────────────────────────────────
    # Two routes were researched, each with its own hypothesis and its own way
    # of measuring it, and until now the studio rendered one set of artwork from
    # route A. A test you cannot run is not a test, so each route gets a poster
    # of its own: same register, same product, same offer — only the headline
    # differs, which is the variable the routes actually disagree about.
    #
    # One poster per route rather than a second full kit. The comparison needs a
    # pair a person can hold side by side, not twice the render bill.
    ab_routes = [r.route_id for r in plan.creative_routes[:2] if r.route_id]
    if len(ab_routes) >= 2:
        ab_platform = (draft_.platforms or ["shopee"])[0]
        for route_id in ab_routes:
            variant = _campaign_texts(plan, campaign_input, route_id)
            nodes.append(NodeSpec(
                id=f"ab_poster_{route_id.lower()}",
                kind="poster",
                deps=["hero"],
                ratio="4:5",
                platform=ab_platform,
                prompt=_route_scene(plan, route_id),
                texts=variant,
                route=route_id,
            ))

    if with_video:
        roles = ["hook", "product", "benefit", "cta"]
        clip_ids: list[str] = []
        vsecs = max(4, min(15, round(draft_.video_seconds / max(1, draft_.video_shots))))
        for i in range(draft_.video_shots):
            role = roles[i] if i < len(roles) else "product"
            kf = f"keyframe_{i}"
            nodes.append(NodeSpec(
                id=kf, kind="keyframe", deps=["hero"], ratio="9:16",
                platform="tiktok_shop" if "tiktok_shop" in draft_.platforms else platform,
                prompt=_shot_scene(role, plan, campaign_input),
                texts=[("headline", _shot_text(role, texts))] if _shot_text(role, texts) else [],
                role=role, seconds=vsecs))
            nodes.append(NodeSpec(id=f"clip_{i}", kind="clip", deps=[kf], ratio="9:16",
                                  platform="tiktok_shop", role=role, seconds=vsecs))
            clip_ids.append(f"clip_{i}")
        nodes.append(NodeSpec(id="voiceover", kind="voiceover", deps=["inventory"]))
        nodes.append(NodeSpec(id="master", kind="assemble", deps=clip_ids + ["voiceover"],
                              ratio="9:16", platform="tiktok_shop"))

    del label
    return GraphSpec(nodes=nodes,
                     rationale=draft_.summary,
                     repaired=[])


def _route_scene(plan: CampaignPlan, route_id: str) -> str:
    """Staging for one route's poster, taken from what that route asked for.

    Upstream writes `visual_direction` per route and the two routes stage the
    product differently on purpose. Using the same scene for both would make the
    pair differ only in lettering, which tests typography rather than the idea.
    """
    route = next((r for r in plan.creative_routes if r.route_id == route_id), None)
    if route is None:
        return "the product, staged for a marketplace poster"
    scene = wording.shorten(getattr(route, "visual_direction", "") or "", 220, slack=60)
    return scene or "the product, staged for a marketplace poster"


def _campaign_texts(plan: CampaignPlan,
                    campaign_input: CampaignInput | None,
                    route_id: str = "") -> list[tuple[str, str]]:
    """The strings this campaign puts on screen, filtered for forbidden claims.

    `route_id` selects which creative route's headline to set. Without it this
    always used `creative_routes[0]`, which is why a plan with two deliberately
    different routes produced one set of artwork: the A/B test existed on paper
    and there was nothing to run it with. The offer and the call to action are
    the same either way — they are facts about the campaign, not about the
    argument being tested.
    """
    banned = [c.casefold() for c in (campaign_input.product_brief.forbidden_claims
                                     if campaign_input else []) if c.strip()]

    def ok(value: str) -> bool:
        low = (value or "").casefold()
        return bool(value.strip()) and not any(b in low for b in banned)

    route = next((r for r in plan.creative_routes if r.route_id == route_id),
                 plan.creative_routes[0] if plan.creative_routes else None)
    out: list[tuple[str, str]] = []
    for role, value in (
        ("headline", _headline(route, plan)),
        ("badge", _badge(campaign_input)),
        ("cta", "MUA NGAY"),
    ):
        if ok(value):
            out.append((role, value))
    return out


# A slogan is short. Anything past this is prose, and prose on a poster reads as
# a mistake even when every character is correct.
_MAX_HEADLINE = 42
_MAX_BADGE = 22


def _headline(route: Any, plan: CampaignPlan) -> str:
    """The line that goes on the poster, which is rarely `hook_idea` verbatim.

    Upstream writes `hook_idea` as a shot description — "Cận cảnh bàn tay lật
    gói G7, đổ bột vào cốc… Dòng chữ nhảy ra: 'Mệt buổi sáng?'" — so taking it
    whole prints the director's stage direction onto the artwork. The slogan is
    usually inside the quotation marks.

    A long quoted line is shortened, never abandoned. Falling back to the
    positioning line because the route's own hook ran past a character count is
    what collapsed the A/B test on the real G7 plan: route A's nineteen-word
    hook was dropped and replaced by the same "C\u00e0 ph\u00ea \u0111\u1eadm v\u1ecb Robusta Bu\u00f4n Ma
    Thu\u1ed9t" that route B already carried, so two deliberately different creative
    routes came back saying one thing. The positioning line is the fallback for
    a route with no hook at all, not for a route whose hook is wordy.
    """
    hook = (getattr(route, "hook_idea", "") or "").strip()
    for opener, closer in (("'", "'"), ("\u2018", "\u2019"), ("\u201c", "\u201d"), ('"', '"')):
        start = hook.find(opener)
        end = hook.find(closer, start + 1)
        if start != -1 and end > start + 1:
            quoted = hook[start + 1:end].strip()
            if len(quoted) > 3:
                return wording.shorten(quoted, _MAX_HEADLINE)

    if hook:
        return wording.shorten(hook, _MAX_HEADLINE)
    return wording.shorten(plan.positioning.key_selling_message, _MAX_HEADLINE)


def _badge(campaign_input: CampaignInput | None) -> str:
    """The offer, as a badge reads it: a few words, upper case.

    "Cross-border 9.9: mua 3 tặng 1 và miễn phí vận chuyển" is the offer; the
    badge wants "MUA 3 TẶNG 1". Pull the strongest fragment rather than
    truncating, because a truncated offer is worse than a short one.

    A brief with a price but no promotion falls back to the price, which is a
    legitimate badge on a marketplace listing — but to a *whole* price.
    Character truncation produced `135.000Đ / TÚI 50 GÓI ·` here: a badge that
    ends on its own separator and promises nothing.
    """
    raw = (campaign_input.product_brief.price_or_promotion if campaign_input else "") or ""
    return (wording.offer_badge(raw, _MAX_BADGE)
            or wording.shorten(raw, _MAX_BADGE).upper())


# Both helpers moved to `wording.py`. They existed here and, in a second and
# subtly different form, in `direct.py` — which is how the same G7 offer became
# "MUA 3 TẶNG 1" on the approval screen and "135.000Đ / TÚI 50 GÓI ·" on the
# worksheet. One implementation, imported by both.
_strip_label = wording.strip_label


def _trim(text: str, limit: int) -> str:
    """Shorten copy to fit a frame. Kept as a name because callers read better
    for it; the behaviour is `wording.shorten`."""
    return wording.shorten(text, limit)


def _shot_scene(role: str, plan: CampaignPlan,
                campaign_input: CampaignInput | None) -> str:
    """Staging for one beat, drawn from the brief rather than invented."""
    signal = campaign_input.market_signal if campaign_input else None
    brief = campaign_input.product_brief if campaign_input else None
    return {
        "hook": (signal.consumer_pain_point if signal and signal.consumer_pain_point
                 else "the product arriving in frame"),
        "product": "the product held towards the camera, label facing forward",
        "benefit": (brief.key_selling_points[0] if brief and brief.key_selling_points
                    else plan.positioning.key_selling_message),
        "cta": (brief.price_or_promotion if brief and brief.price_or_promotion
                else "the product with the offer beside it"),
    }.get(role, "the product, centred")


def _shot_text(role: str, texts: list[tuple[str, str]]) -> str:
    lookup = dict(texts)
    return {"hook": lookup.get("headline", ""), "cta": lookup.get("badge", "")}.get(role, "")


def to_dict(spec: GraphSpec) -> dict[str, Any]:
    """Serialise a spec for the UI and for `data/<campaign>/graph.json`."""
    return {
        "rationale": spec.rationale,
        "repaired": spec.repaired,
        "nodes": [
            {"id": n.id, "kind": n.kind, "deps": n.deps, "ratio": n.ratio,
             "platform": n.platform, "prompt": n.prompt,
             "texts": [list(t) for t in n.texts], "role": n.role, "seconds": n.seconds}
            for n in spec.nodes
        ],
    }


def draft_to_dict(d: Draft) -> dict[str, Any]:
    return {
        "summary": d.summary, "platforms": d.platforms,
        "register": {
            "name": d.register.name, "lens": d.register.lens, "light": d.register.light,
            "surface": d.register.surface, "grade": d.register.grade,
            "palette": d.register.palette, "why": d.register.why,
            "source": d.register.source,
        },
        "video_shots": d.video_shots, "video_seconds": d.video_seconds,
        "notes": d.notes,
        "deliverables": [
            {"id": x.id, "kind": x.kind, "platform": x.platform,
             "ratio": x.ratio, "purpose": x.purpose}
            for x in d.deliverables
        ],
    }
