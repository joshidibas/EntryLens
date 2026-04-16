from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path


MARKER_START = "<!-- graphify-links:start -->"
MARKER_END = "<!-- graphify-links:end -->"
CODE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".ps1",
    ".sql",
    ".css",
    ".scss",
    ".html",
    ".yml",
    ".yaml",
    ".toml",
    ".md",
}


@dataclass
class EdgeView:
    relation: str
    confidence: str
    confidence_score: float
    other_id: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an Obsidian-friendly wiki from graphify output."
    )
    parser.add_argument(
        "--graph",
        default="graphify-out/graph.json",
        help="Path to graph.json relative to the repo root.",
    )
    parser.add_argument(
        "--wiki-root",
        default="graphify-out/wiki",
        help="Output folder for generated Obsidian notes, relative to the repo root.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def normalize_repo_path(raw: str, root: Path) -> str | None:
    text = raw.strip().strip("<>").strip()
    if not text:
        return None
    text = text.split("#", 1)[0]
    text = text.split("?", 1)[0]
    text = text.replace("\\", "/")

    lowered = text.lower()
    root_str = root.as_posix().lower()
    if lowered.startswith(root_str):
        text = text[len(root.as_posix()) :].lstrip("/")
    elif re.match(r"^[a-zA-Z]:/", text):
        try:
            candidate = Path(text)
            rel = candidate.resolve().relative_to(root.resolve())
            text = rel.as_posix()
        except Exception:
            return None
    elif text.startswith("/"):
        text = text.lstrip("/")
        if not text.lower().startswith(root_str):
            return None
        text = text[len(root.as_posix()) :].lstrip("/")

    candidate = root / Path(text)
    if candidate.exists():
        return candidate.relative_to(root).as_posix()
    return text if not text.startswith("http") else None


def markdown_wikilink(repo_rel_md_path: str, label: str | None = None) -> str:
    target = repo_rel_md_path[:-3] if repo_rel_md_path.endswith(".md") else repo_rel_md_path
    if label:
        return f"[[{target}|{label}]]"
    return f"[[{target}]]"


def code_wikilink(repo_rel_path: str, label: str | None = None) -> str:
    if label:
        return f"[[{repo_rel_path}|{label}]]"
    return f"[[{repo_rel_path}]]"


def safe_yaml(text: str) -> str:
    return text.replace('"', "'")


def load_graph(graph_path: Path) -> dict:
    return json.loads(graph_path.read_text(encoding="utf-8"))


def parse_line_number(source_location: str) -> int:
    match = re.search(r"L(\d+)", source_location or "")
    return int(match.group(1)) if match else 0


def is_file_node(node: dict) -> bool:
    source_file = node.get("source_file") or ""
    return bool(source_file) and Path(source_file).name == (node.get("label") or "")


def top_ids_by_degree(node_ids: list[str], degree_map: Counter, limit: int) -> list[str]:
    return sorted(node_ids, key=lambda node_id: (-degree_map[node_id], node_id))[:limit]


def extract_doc_references(doc_path: Path, root: Path) -> set[str]:
    text = doc_path.read_text(encoding="utf-8")
    refs: set[str] = set()

    for raw in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        normalized = normalize_repo_path(raw, root)
        if normalized:
            refs.add(normalized)

    for raw in re.findall(r"`([^`\n]+)`", text):
        normalized = normalize_repo_path(raw, root)
        if normalized and Path(normalized).suffix.lower() in CODE_EXTENSIONS:
            refs.add(normalized)

    return refs


def replace_generated_block(text: str, new_block: str) -> str:
    pattern = re.compile(
        rf"\n?{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}\n?",
        flags=re.DOTALL,
    )
    if pattern.search(text):
        updated = pattern.sub(f"\n\n{new_block}\n", text).rstrip() + "\n"
        return updated
    return text.rstrip() + f"\n\n{new_block}\n"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def render_file_note(
    repo_rel: str,
    note_rel: str,
    file_nodes: list[dict],
    file_note_path: Path,
    source_file_to_docs: dict[str, list[str]],
    source_file_to_related: dict[str, list[str]],
    source_file_to_note: dict[str, str],
    node_to_note: dict[str, str],
    community_note_paths: dict[int, str],
    degree_map: Counter,
) -> None:
    file_level = next((node for node in file_nodes if is_file_node(node)), None)
    community = file_level.get("community") if file_level else None
    symbols = [
        node
        for node in sorted(file_nodes, key=lambda item: parse_line_number(item.get("source_location", "")))
        if not is_file_node(node)
    ]
    rationale_nodes = [node for node in symbols if node.get("file_type") == "rationale"]
    code_symbols = [node for node in symbols if node.get("file_type") != "rationale"]

    lines = [
        "---",
        f'title: "{safe_yaml(repo_rel)}"',
        "tags:",
        "  - graphify/file",
        "---",
        "",
        f"# {repo_rel}",
        "",
        f"- Source file: {code_wikilink(repo_rel, Path(repo_rel).name)}",
    ]

    if community is not None:
        lines.append(
            f"- Community: {markdown_wikilink(community_note_paths[community], f'Community {community}')}"
        )
    lines.append("")

    if rationale_nodes:
        lines.extend(["## Rationale", ""])
        for node in rationale_nodes[:3]:
            lines.append(f"- {node.get('label', '').strip()}")
        lines.append("")

    if code_symbols:
        lines.extend(["## Symbols", ""])
        for node in code_symbols[:25]:
            label = node.get("label", node["id"])
            lines.append(f"- {markdown_wikilink(node_to_note[node['id']], label)}")
        lines.append("")

    related_files = source_file_to_related.get(repo_rel, [])
    if related_files:
        lines.extend(["## Related Files", ""])
        for related in related_files[:15]:
            related_note = source_file_to_note.get(related)
            label = f"{Path(related).name} ({degree_map.get(next((n['id'] for n in file_nodes if n.get('source_file', '').replace('\\\\', '/').replace('\\', '/') == repo_rel), ''), 0)} edges)"
            if related_note:
                lines.append(
                    f"- {markdown_wikilink(related_note, Path(related).name)}"
                )
            else:
                lines.append(f"- {code_wikilink(related, Path(related).name)}")
        lines.append("")

    docs = source_file_to_docs.get(repo_rel, [])
    if docs:
        lines.extend(["## Referenced By Docs", ""])
        for doc in docs[:15]:
            lines.append(f"- {markdown_wikilink(doc, Path(doc).stem)}")
        lines.append("")

    file_note_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def render_node_note(
    node: dict,
    note_path: Path,
    node_to_note: dict[str, str],
    source_file_to_note: dict[str, str],
    node_edges: list[EdgeView],
    nodes_by_id: dict[str, dict],
    source_file_to_docs: dict[str, list[str]],
    community_note_paths: dict[int, str],
    degree_map: Counter,
) -> None:
    label = node.get("label", node["id"])
    source_file = (node.get("source_file") or "").replace("\\", "/")
    community = node.get("community")
    lines = [
        "---",
        f'title: "{safe_yaml(label)}"',
        "tags:",
        "  - graphify/node",
        f"  - graphify/{node.get('file_type', 'code')}",
        "---",
        "",
        f"# {label}",
        "",
        f"- Node ID: `{node['id']}`",
        f"- Type: `{node.get('file_type', 'code')}`",
    ]

    if source_file:
        source_note = source_file_to_note.get(source_file)
        if source_note:
            lines.append(
                f"- Source file: {markdown_wikilink(source_note, Path(source_file).name)}"
            )
        else:
            lines.append(f"- Source file: {code_wikilink(source_file, Path(source_file).name)}")
    if node.get("source_location"):
        lines.append(f"- Location: `{node['source_location']}`")
    if community is not None:
        lines.append(
            f"- Community: {markdown_wikilink(community_note_paths[community], f'Community {community}')}"
        )
    lines.append(f"- Degree: `{degree_map[node['id']]}`")
    lines.append("")

    docs = source_file_to_docs.get(source_file, [])
    if docs:
        lines.extend(["## Related Docs", ""])
        for doc in docs[:10]:
            lines.append(f"- {markdown_wikilink(doc, Path(doc).stem)}")
        lines.append("")

    if node_edges:
        lines.extend(["## Linked Nodes", ""])
        sorted_edges = sorted(
            node_edges,
            key=lambda edge: (-edge.confidence_score, edge.relation, edge.other_id),
        )
        for edge in sorted_edges[:20]:
            other = nodes_by_id[edge.other_id]
            other_label = other.get("label", other["id"])
            lines.append(
                f"- `{edge.relation}` -> {markdown_wikilink(node_to_note[other['id']], other_label)} ({edge.confidence})"
            )
        lines.append("")

    note_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def render_community_note(
    community: int,
    note_path: Path,
    note_rel: str,
    node_ids: list[str],
    nodes_by_id: dict[str, dict],
    node_to_note: dict[str, str],
    source_file_to_note: dict[str, str],
    source_file_to_docs: dict[str, list[str]],
    degree_map: Counter,
) -> None:
    nodes = [nodes_by_id[node_id] for node_id in node_ids]
    file_nodes = [
        node
        for node in nodes
        if node.get("source_file") and is_file_node(node)
    ]
    symbol_nodes = [node for node in nodes if not is_file_node(node) and node.get("file_type") != "rationale"]

    docs = sorted(
        {
            doc
            for node in nodes
            for doc in source_file_to_docs.get((node.get("source_file") or "").replace("\\", "/"), [])
        }
    )

    lines = [
        "---",
        f'title: "Community {community}"',
        "tags:",
        "  - graphify/community",
        "---",
        "",
        f"# Community {community}",
        "",
        f"- Node count: `{len(node_ids)}`",
        "",
    ]

    if file_nodes:
        lines.extend(["## Files", ""])
        for node in sorted(file_nodes, key=lambda item: (-degree_map[item["id"]], item.get("label", "")))[:20]:
            source_file = (node.get("source_file") or "").replace("\\", "/")
            note = source_file_to_note.get(source_file)
            label = source_file
            if note:
                lines.append(f"- {markdown_wikilink(note, label)}")
            else:
                lines.append(f"- {code_wikilink(source_file, label)}")
        lines.append("")

    if symbol_nodes:
        lines.extend(["## Hot Symbols", ""])
        for node in sorted(symbol_nodes, key=lambda item: (-degree_map[item["id"]], item.get("label", "")))[:20]:
            lines.append(
                f"- {markdown_wikilink(node_to_note[node['id']], node.get('label', node['id']))}"
            )
        lines.append("")

    if docs:
        lines.extend(["## Related Docs", ""])
        for doc in docs[:15]:
            lines.append(f"- {markdown_wikilink(doc, Path(doc).stem)}")
        lines.append("")

    note_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = repo_root()
    graph_path = root / args.graph
    wiki_root = root / args.wiki_root

    graph = load_graph(graph_path)
    nodes = graph.get("nodes", [])
    edges = graph.get("links") or graph.get("edges") or []
    nodes_by_id = {node["id"]: node for node in nodes}

    degree_map: Counter = Counter()
    adjacency: dict[str, list[EdgeView]] = defaultdict(list)
    community_to_node_ids: dict[int, list[str]] = defaultdict(list)

    for node in nodes:
        community_to_node_ids[int(node.get("community", -1))].append(node["id"])

    for edge in edges:
        src = edge.get("_src") or edge.get("source")
        tgt = edge.get("_tgt") or edge.get("target")
        if not src or not tgt or src not in nodes_by_id or tgt not in nodes_by_id:
            continue
        relation = edge.get("relation", "related_to")
        confidence = edge.get("confidence", "UNKNOWN")
        score = float(edge.get("confidence_score", 0.0) or 0.0)
        degree_map[src] += 1
        degree_map[tgt] += 1
        adjacency[src].append(EdgeView(relation, confidence, score, tgt))
        adjacency[tgt].append(EdgeView(relation, confidence, score, src))

    source_file_to_nodes: dict[str, list[dict]] = defaultdict(list)
    for node in nodes:
        source_file = (node.get("source_file") or "").replace("\\", "/")
        if source_file:
            source_file_to_nodes[source_file].append(node)

    source_file_to_note: dict[str, str] = {}
    for source_file in sorted(source_file_to_nodes):
        source_file_to_note[source_file] = f"{args.wiki_root}/{source_file}.md"

    node_to_note: dict[str, str] = {}
    for node in nodes:
        node_to_note[node["id"]] = f"{args.wiki_root}/nodes/{node['id']}.md"

    community_note_paths = {
        community: f"{args.wiki_root}/communities/Community {community}.md"
        for community in sorted(community_to_node_ids)
        if community >= 0
    }

    source_file_to_related: dict[str, Counter] = defaultdict(Counter)
    for source_file, file_nodes in source_file_to_nodes.items():
        for node in file_nodes:
            for edge in adjacency.get(node["id"], []):
                other = nodes_by_id[edge.other_id]
                other_file = (other.get("source_file") or "").replace("\\", "/")
                if other_file and other_file != source_file:
                    source_file_to_related[source_file][other_file] += 1

    doc_paths = sorted(
        path
        for path in root.rglob("*.md")
        if "graphify-out/wiki" not in rel_posix(path, root)
        and "graphify-out/cache" not in rel_posix(path, root)
    )
    doc_paths = [
        path
        for path in doc_paths
        if rel_posix(path, root).startswith("docs/")
        or path.name in {
            "AGENTS.md",
            "ENTRYLENS_ARCHITECTURE.md",
            "ENTRYLENS_MASTER_PLAN.md",
            "ENTRYLENS_BUILD_PLAN.md",
        }
    ]

    source_file_to_docs: dict[str, list[str]] = defaultdict(list)
    doc_to_source_files: dict[str, list[str]] = defaultdict(list)
    for doc_path in doc_paths:
        repo_doc = rel_posix(doc_path, root)
        refs = extract_doc_references(doc_path, root)
        source_refs = sorted(
            {
                ref
                for ref in refs
                if ref in source_file_to_note and not ref.endswith(".md")
            }
        )
        doc_to_source_files[repo_doc] = source_refs
        for source_ref in source_refs:
            source_file_to_docs[source_ref].append(repo_doc)

    if wiki_root.exists():
        shutil.rmtree(wiki_root)
    ensure_dir(wiki_root)
    ensure_dir(wiki_root / "nodes")
    ensure_dir(wiki_root / "communities")

    for source_file, file_nodes in source_file_to_nodes.items():
        note_path = root / source_file_to_note[source_file]
        ensure_dir(note_path.parent)
        render_file_note(
            repo_rel=source_file,
            note_rel=source_file_to_note[source_file],
            file_nodes=file_nodes,
            file_note_path=note_path,
            source_file_to_docs=source_file_to_docs,
            source_file_to_related={
                key: [item[0] for item in counter.most_common(15)]
                for key, counter in source_file_to_related.items()
            },
            source_file_to_note=source_file_to_note,
            node_to_note=node_to_note,
            community_note_paths=community_note_paths,
            degree_map=degree_map,
        )

    for node in nodes:
        note_path = root / node_to_note[node["id"]]
        ensure_dir(note_path.parent)
        render_node_note(
            node=node,
            note_path=note_path,
            node_to_note=node_to_note,
            source_file_to_note=source_file_to_note,
            node_edges=adjacency.get(node["id"], []),
            nodes_by_id=nodes_by_id,
            source_file_to_docs=source_file_to_docs,
            community_note_paths=community_note_paths,
            degree_map=degree_map,
        )

    for community, node_ids in community_to_node_ids.items():
        if community < 0:
            continue
        note_path = root / community_note_paths[community]
        ensure_dir(note_path.parent)
        render_community_note(
            community=community,
            note_path=note_path,
            note_rel=community_note_paths[community],
            node_ids=node_ids,
            nodes_by_id=nodes_by_id,
            node_to_note=node_to_note,
            source_file_to_note=source_file_to_note,
            source_file_to_docs=source_file_to_docs,
            degree_map=degree_map,
        )

    top_nodes = top_ids_by_degree([node["id"] for node in nodes], degree_map, limit=15)
    top_docs = sorted(doc_to_source_files, key=lambda doc: (-len(doc_to_source_files[doc]), doc))[:12]
    community_counts = sorted(
        ((community, len(node_ids)) for community, node_ids in community_to_node_ids.items() if community >= 0),
        key=lambda item: (-item[1], item[0]),
    )

    index_lines = [
        "---",
        'title: "Graphify Wiki"',
        "tags:",
        "  - graphify/index",
        "---",
        "",
        "# Graphify Wiki",
        "",
        f"Generated on {date.today().isoformat()} from `{args.graph}`.",
        "",
        "## Start Here",
        "",
        f"- Report: {markdown_wikilink('graphify-out/GRAPH_REPORT.md', 'GRAPH_REPORT')}",
        "- View this repository as an Obsidian vault rooted at the repo folder.",
        "- Rebuild the code graph with `graphify update .`, then rerun this exporter.",
        "",
        "## Key Docs",
        "",
    ]
    for doc in top_docs:
        index_lines.append(f"- {markdown_wikilink(doc, doc)}")
    index_lines.extend(["", "## Communities", ""])
    for community, count in community_counts[:20]:
        index_lines.append(
            f"- {markdown_wikilink(community_note_paths[community], f'Community {community}')} ({count} nodes)"
        )
    index_lines.extend(["", "## Hot Nodes", ""])
    for node_id in top_nodes:
        node = nodes_by_id[node_id]
        index_lines.append(
            f"- {markdown_wikilink(node_to_note[node_id], node.get('label', node_id))} ({degree_map[node_id]} edges)"
        )
    index_lines.extend(["", "## File Notes", ""])
    for source_file in sorted(source_file_to_note)[:40]:
        index_lines.append(
            f"- {markdown_wikilink(source_file_to_note[source_file], source_file)}"
        )
    (wiki_root / "index.md").write_text("\n".join(index_lines).rstrip() + "\n", encoding="utf-8")

    skipped_docs = []

    for doc_path in doc_paths:
        repo_doc = rel_posix(doc_path, root)
        source_files = doc_to_source_files.get(repo_doc, [])
        community_ids = sorted(
            {
                int(next(iter({node.get("community", -1) for node in source_file_to_nodes[source_file]})))
                for source_file in source_files
                if source_file in source_file_to_nodes
            }
        )
        block_lines = [
            MARKER_START,
            "## Graph Links",
            "",
            f"- {markdown_wikilink('graphify-out/wiki/index.md', 'Graphify Wiki')}",
            f"- {markdown_wikilink('graphify-out/GRAPH_REPORT.md', 'Graph Report')}",
        ]
        if source_files:
            block_lines.append("- Related file notes:")
            for source_file in source_files[:12]:
                block_lines.append(
                    f"  - {markdown_wikilink(source_file_to_note[source_file], source_file)}"
                )
        if community_ids:
            block_lines.append("- Related communities:")
            for community in community_ids[:6]:
                if community in community_note_paths:
                    block_lines.append(
                        f"  - {markdown_wikilink(community_note_paths[community], f'Community {community}')}"
                    )
        block_lines.append(MARKER_END)
        updated_text = replace_generated_block(
            doc_path.read_text(encoding="utf-8"),
            "\n".join(block_lines),
        )
        try:
            doc_path.write_text(updated_text, encoding="utf-8")
        except PermissionError as exc:
            skipped_docs.append(
                {
                    "path": str(doc_path),
                    "reason": f"permission denied: {exc}",
                }
            )

    print(
        json.dumps(
            {
                "wiki_root": args.wiki_root,
                "file_notes": len(source_file_to_note),
                "node_notes": len(node_to_note),
                "communities": len(community_note_paths),
                "docs_updated": len(doc_paths),
                "docs_skipped": skipped_docs,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
