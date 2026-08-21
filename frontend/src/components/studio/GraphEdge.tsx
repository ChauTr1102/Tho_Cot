"use client";

/**
 * A connector between two nodes, drawn to be read rather than to decorate.
 *
 * The edge carries three states and each one answers a question a viewer is
 * actually asking while a run grinds through its tenth minute:
 *
 *   idle     "these are related"        — a hairline, low contrast, no motion.
 *   active   "work is moving down here" — lime, and the dashes crawl towards
 *            the downstream node. Only ever while that node is running, so at
 *            any moment the number of moving edges equals the number of things
 *            actually happening.
 *   dead     "this branch is finished,  — flat grey, no motion. Whole subtrees
 *            and not in a good way"       go grey together, which is what makes
 *                                         a failure legible at a glance.
 *
 * A fourth, quieter distinction: once both ends have succeeded the edge firms
 * up slightly, so a completed region of the graph reads as solid and the
 * frontier of the run reads as faint.
 *
 * Motion is CSS, not React: an animated edge never re-renders, it just has a
 * class. `prefers-reduced-motion` drops the crawl and keeps the colour, since
 * "this edge is live" is information and not flair.
 */

import { memo } from "react";
import { BaseEdge, getBezierPath, type Edge, type EdgeProps } from "@xyflow/react";

/** A `type`, not an `interface`: React Flow requires `Record<string, unknown>`. */
export type GraphEdgeData = {
  /** The downstream node is working right now. */
  active: boolean;
  /** Downstream of a failure — the branch is over. */
  dead: boolean;
  /** Both endpoints reached a successful terminal state. */
  settled: boolean;
};

export type GraphFlowEdge = Edge<GraphEdgeData, "studio">;

function GraphEdgeLine({
  sourceX,
  sourceY,
  sourcePosition,
  targetX,
  targetY,
  targetPosition,
  data,
}: EdgeProps<GraphFlowEdge>) {
  const [path] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    // Gentler than the default: columns are close together and a hard S-bend
    // between neighbouring layers reads as a knot.
    curvature: 0.32,
  });

  const state = data?.dead
    ? "dead"
    : data?.active
      ? "active"
      : data?.settled
        ? "settled"
        : "idle";

  return (
    <>
      <BaseEdge path={path} className="studio-edge" data-state={state} />
      {/* The crawling dashes ride a second path on top of the base line, so
          the connector never disappears between dashes. */}
      {state === "active" ? (
        <path d={path} className="studio-edge-flow" fill="none" />
      ) : null}
    </>
  );
}

export const GraphEdge = memo(GraphEdgeLine);
