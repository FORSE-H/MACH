#!/usr/bin/env python3
"""build_graph.py — emit graph.json, the reuse graph over the catalogue.

Reads every entry's JSON-LD and derives a node/edge graph showing how the
catalogue is connected:

  nodes  = entries (the tools/models/datasets) + the controlled hubs they share:
           standards, programming languages, and organisations
  edges  = implements  (entry  -> standard,  from mach:supportsSpec)
           written-in  (entry  -> language,  from programmingLanguage)
           by-org      (entry  -> org,       from mach:foundation)

This is "Layer A" — built purely from data already in the entries. The dependency
layer (entry -> entry, "pydicom used by N tools") will be added once mach:dependsOn
is harvested; this builder is written so those edges slot in without reshaping it.

Deterministic and rebuildable, like generate_entries / signals: same input → same
graph.json. The site's graph.html renders it with Cytoscape.js.

Usage:
    python scripts/build_graph.py            # writes graph.json
    python scripts/build_graph.py --out graph.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ENTRIES = Path("entries")
_DEFAULT_OUT = Path("graph.json")


def _listify(v):
    return v if isinstance(v, list) else ([v] if v else [])


def _spec_id(s: str) -> str:
    """Normalise a supportsSpec value (a full @id URL or a short name) to one id."""
    s = str(s)
    if "entries/specs/" in s:
        return s.rstrip("/").split("/")[-1]
    return s.lower().strip().replace(" ", "-")


def _category(entry: dict) -> str:
    return entry.get("mach:category", "software")


def build() -> dict:
    entries = []
    for f in sorted(ENTRIES.rglob("*.jsonld")):
        if f.name.startswith("_"):
            continue
        try:
            entries.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(node_id: str, label: str, ntype: str) -> None:
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "label": label, "type": ntype, "degree": 0}

    def add_edge(src: str, dst: str, etype: str) -> None:
        edges.append({"source": src, "target": dst, "type": etype})
        nodes[src]["degree"] = nodes.get(src, {}).get("degree", 0) + 1
        nodes[dst]["degree"] = nodes.get(dst, {}).get("degree", 0) + 1

    # Entry nodes first, so edges can reference them.
    for e in entries:
        ident = e.get("identifier")
        if not ident:
            continue
        add_node(f"entry:{ident}", e.get("name", ident), f"entry:{_category(e)}")

    # Hub nodes + edges.
    for e in entries:
        ident = e.get("identifier")
        if not ident:
            continue
        src = f"entry:{ident}"

        for s in _listify(e.get("mach:supportsSpec")):
            sid = _spec_id(s)
            nid = f"standard:{sid}"
            add_node(nid, sid.upper().replace("-", " "), "standard")
            add_edge(src, nid, "implements")

        for lang in _listify(e.get("programmingLanguage")):
            nid = f"lang:{lang}"
            add_node(nid, lang, "language")
            add_edge(src, nid, "written-in")

        org = e.get("mach:foundation")
        if org:
            nid = f"org:{org}"
            add_node(nid, org, "org")
            add_edge(src, nid, "by-org")

    # Drop singleton hubs (an org/language/standard linking only one entry adds
    # noise, not structure). Keep every entry node.
    hub_degree = Counter()
    for ed in edges:
        hub_degree[ed["target"]] += 1
    keep = {
        nid for nid, n in nodes.items()
        if n["type"].startswith("entry:") or hub_degree[nid] >= 2
    }
    nodes = {nid: n for nid, n in nodes.items() if nid in keep}
    edges = [ed for ed in edges if ed["source"] in keep and ed["target"] in keep]

    # Recompute degree after pruning (so node size reflects the final graph).
    deg = Counter()
    for ed in edges:
        deg[ed["source"]] += 1
        deg[ed["target"]] += 1
    for nid, n in nodes.items():
        n["degree"] = deg[nid]

    type_counts = Counter(n["type"].split(":")[0] for n in nodes.values())
    edge_counts = Counter(ed["type"] for ed in edges)

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "meta": {
            "entry_count": sum(1 for n in nodes.values() if n["type"].startswith("entry:")),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": dict(type_counts),
            "edge_types": dict(edge_counts),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = ap.parse_args()

    graph = build()
    args.out.write_text(json.dumps(graph, ensure_ascii=False) + "\n", encoding="utf-8")
    m = graph["meta"]
    print(
        f"Wrote {args.out}: {m['node_count']} nodes, {m['edge_count']} edges "
        f"({m['entry_count']} entries; hubs {m['node_types']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
