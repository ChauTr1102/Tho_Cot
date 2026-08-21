/**
 * Geometry for the studio canvas: how big a node is, and where it starts.
 *
 * Two rules the rest of the canvas depends on:
 *
 *  1. **A node's size is a pure function of its kind.** It is decided before
 *     the node has run and never changes afterwards, so a thumbnail landing
 *     mid-run cannot reflow the board under a viewer who is reading it. The
 *     cost is a media well that stands empty until its picture arrives — which
 *     is the honest shape of the wait anyway, and reads as a slot being filled
 *     rather than as the canvas growing.
 *
 *  2. **Layout runs on the graph's shape, not on its state.** The `graph`
 *     event carries every node and every edge before anything starts, so the
 *     arrangement is computed exactly once per run. Node events after that
 *     touch one node's data and move nothing.
 */

import type { GraphNodeSpec, NodeKind } from "@/types/studio";

/* ──────────────────────────────────────────────────────────────────────────
 * Node size
 * ────────────────────────────────────────────────────────────────────────── */

/**
 * Card width, by whether the node has a picture to show.
 *
 * A node carrying a preview needs enough width for it to read as a
 * photograph; `inventory` and `worksheet` carry a label and a timer and
 * nothing else, and giving them the same 232px would spend two whole columns
 * of a six-column board on two one-line chips. The board is wide and the
 * viewport is not, so every column that can be narrow should be.
 */
const WIDTH_MEDIA = 232;
const WIDTH_PLAIN = 178;

export function nodeWidth(kind: NodeKind): number {
  return isMediaKind(kind) ? WIDTH_MEDIA : WIDTH_PLAIN;
}

/** Kinds that produce a file worth previewing on the node. */
const MEDIA_KINDS: ReadonlySet<string> = new Set([
  "image",
  "keyframe",
  "video",
  "compose",
  "cutdown",
]);

/**
 * Kinds rendered from a prompt, and therefore worth re-running with a new one.
 *
 * `compose` is excluded deliberately: the master video is ffmpeg concatenating
 * clips, so there is no prompt to edit and offering a box would be a lie.
 */
const PROMPT_KINDS: ReadonlySet<string> = new Set(["image", "keyframe", "video"]);

export function isMediaKind(kind: NodeKind): boolean {
  return MEDIA_KINDS.has(kind);
}

export function isPromptKind(kind: NodeKind): boolean {
  return PROMPT_KINDS.has(kind);
}

/* Heights are stated in px, not rem, because the layout arithmetic below is in
   px and the app's root font size is not guaranteed to be 16. Each figure is
   the card's chrome (padding, header, meta row, prompt block) plus the space
   left over for the preview well, which is the only element that flexes. */
const HEIGHT_WITH_PROMPT = 264; // ~127px of preview
const HEIGHT_MEDIA_ONLY = 196; // ~127px of preview
const HEIGHT_PLAIN = 66; // header + meta only

export function nodeHeight(kind: NodeKind): number {
  if (isPromptKind(kind)) return HEIGHT_WITH_PROMPT;
  if (isMediaKind(kind)) return HEIGHT_MEDIA_ONLY;
  return HEIGHT_PLAIN;
}

/* ──────────────────────────────────────────────────────────────────────────
 * Layout
 * ────────────────────────────────────────────────────────────────────────── */

const COLUMN_GAP = 74;
const ROW_GAP = 18;

export interface Point {
  x: number;
  y: number;
}

/**
 * Depth of every node: 0 for a root, otherwise one past its deepest dependency.
 *
 * Longest-path rather than shortest, so an edge always points strictly
 * rightwards and no connector ever doubles back. A cycle is impossible in a
 * validated DAG but is guarded anyway — a malformed `graph` event must not
 * hang the render.
 */
function computeDepths(specs: readonly GraphNodeSpec[]): Map<string, number> {
  const byId = new Map(specs.map((spec) => [spec.id, spec]));
  const depth = new Map<string, number>();

  const resolve = (id: string, seen: Set<string>): number => {
    const cached = depth.get(id);
    if (cached !== undefined) return cached;
    if (seen.has(id)) return 0;

    const spec = byId.get(id);
    const deps = spec?.deps?.filter((dep) => byId.has(dep)) ?? [];

    seen.add(id);
    const value =
      deps.length === 0
        ? 0
        : 1 + Math.max(...deps.map((dep) => resolve(dep, seen)));
    seen.delete(id);

    depth.set(id, value);
    return value;
  };

  for (const spec of specs) resolve(spec.id, new Set<string>());
  return depth;
}

/**
 * Group nodes into dependency layers, left to right.
 *
 * Exported because the empty state draws the same columns as a skeleton, and
 * the two must agree about how many there will be.
 */
export function computeLayers(specs: readonly GraphNodeSpec[]): string[][] {
  const depth = computeDepths(specs);
  const layers: string[][] = [];
  for (const spec of specs) {
    const index = depth.get(spec.id) ?? 0;
    (layers[index] ??= []).push(spec.id);
  }
  for (let index = 0; index < layers.length; index += 1) layers[index] ??= [];
  return layers;
}

/**
 * Arrange the graph into left-to-right dependency layers.
 *
 * Within a layer, nodes are ordered by the average position of their
 * neighbours — the barycentre heuristic, swept forwards then backwards then
 * forwards again. Three sweeps is not optimal crossing reduction and does not
 * need to be: it costs nothing on a 25-node graph and it is the difference
 * between four clips fanning cleanly out of four keyframes and the same eight
 * nodes wired into a braid.
 *
 * Each column is centred on y=0 so the board reads as one horizontal band
 * rather than a staircase.
 */
export function layoutGraph(specs: readonly GraphNodeSpec[]): Map<string, Point> {
  const positions = new Map<string, Point>();
  if (specs.length === 0) return positions;

  const byId = new Map(specs.map((spec) => [spec.id, spec]));
  const layers = computeLayers(specs);

  const dependents = new Map<string, string[]>();
  for (const spec of specs) {
    for (const dep of spec.deps ?? []) {
      if (!byId.has(dep)) continue;
      const list = dependents.get(dep);
      if (list) list.push(spec.id);
      else dependents.set(dep, [spec.id]);
    }
  }

  const rank = new Map<string, number>();
  for (const layer of layers) {
    layer.forEach((id, index) => rank.set(id, index));
  }

  const sweep = (forwards: boolean) => {
    // A forward sweep orders a layer by its parents, so it needs the layer to
    // its left settled first; a backward sweep is the mirror of that.
    const indices = layers.map((_, index) => index);
    const targets = forwards ? indices.slice(1) : indices.slice(0, -1).reverse();

    for (const index of targets) {
      const layer = layers[index];
      if (layer.length < 2) continue;

      const original = new Map(layer.map((id, position) => [id, position]));
      const weight = new Map<string, number>();

      for (const id of layer) {
        const neighbours = forwards
          ? (byId.get(id)?.deps ?? []).filter((dep) => byId.has(dep))
          : (dependents.get(id) ?? []);
        // A node with no neighbours on that side keeps its current place
        // rather than collapsing to the top of the column.
        weight.set(
          id,
          neighbours.length === 0
            ? (original.get(id) ?? 0)
            : neighbours.reduce((sum, n) => sum + (rank.get(n) ?? 0), 0) /
                neighbours.length
        );
      }

      layer.sort(
        (a, b) =>
          (weight.get(a) ?? 0) - (weight.get(b) ?? 0) ||
          (original.get(a) ?? 0) - (original.get(b) ?? 0)
      );
      layer.forEach((id, position) => rank.set(id, position));
    }
  };

  sweep(true);
  sweep(false);
  sweep(true);

  // A column is only as wide as its widest card, so a layer holding nothing
  // but one-line chips does not reserve a picture's worth of horizontal space.
  let columnX = 0;
  layers.forEach((layer) => {
    const kinds = layer.map((id) => byId.get(id)?.kind ?? "plan");
    const heights = kinds.map(nodeHeight);
    const widths = kinds.map(nodeWidth);
    const columnWidth = Math.max(WIDTH_PLAIN, ...widths);

    const span =
      heights.reduce((sum, height) => sum + height, 0) +
      ROW_GAP * Math.max(0, layer.length - 1);

    let y = -span / 2;
    layer.forEach((id, position) => {
      positions.set(id, {
        // Centred in its column, so a mixed layer stays on one vertical axis.
        x: columnX + (columnWidth - widths[position]) / 2,
        y,
      });
      y += heights[position] + ROW_GAP;
    });

    columnX += columnWidth + COLUMN_GAP;
  });

  return positions;
}

/* ──────────────────────────────────────────────────────────────────────────
 * Dead branches
 * ────────────────────────────────────────────────────────────────────────── */

/** Stable identity so "nothing failed" never invalidates a memo. */
const NO_DEAD_NODES: ReadonlySet<string> = new Set<string>();

/**
 * Every node downstream of a failure, transitively.
 *
 * The node that actually failed is *not* in this set — it keeps its red
 * treatment as the root cause, and everything it took with it greys out. One
 * red box at the head of a grey tail says "this is what broke, and this is
 * what it cost" in a way that eight identical red boxes cannot.
 *
 * Computed on the client rather than read from `payload.reason` so a branch
 * greys the instant its ancestor fails, without waiting for the executor's
 * cascade events to arrive one by one.
 */
export function computeDeadBranch(
  nodes: readonly { id: string; deps: string[]; state: string }[]
): ReadonlySet<string> {
  const roots = nodes.filter((node) => node.state === "failed");
  if (roots.length === 0) return NO_DEAD_NODES;

  const dependents = new Map<string, string[]>();
  for (const node of nodes) {
    for (const dep of node.deps) {
      const list = dependents.get(dep);
      if (list) list.push(node.id);
      else dependents.set(dep, [node.id]);
    }
  }

  const dead = new Set<string>();
  const stack = roots.map((node) => node.id);
  while (stack.length > 0) {
    const id = stack.pop() as string;
    for (const child of dependents.get(id) ?? []) {
      if (dead.has(child)) continue;
      dead.add(child);
      stack.push(child);
    }
  }
  return dead.size === 0 ? NO_DEAD_NODES : dead;
}
