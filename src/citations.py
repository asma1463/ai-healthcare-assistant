from pathlib import Path


def format_sources(documents):
    sources = []
    seen = set()

    for index, document in enumerate(documents or [], start=1):
        metadata = getattr(document, "metadata", {}) or {}
        source = metadata.get("source") or metadata.get("file_path") or "Retrieved document"
        source_name = Path(str(source)).name if source else "Retrieved document"

        page = metadata.get("page_label") or metadata.get("page")
        if page is not None:
            try:
                page_label = f"Page {int(page) + 1}"
            except (TypeError, ValueError):
                page_label = f"Page {page}"
            label = f"{source_name} ({page_label})"
        else:
            label = f"{source_name} (Retrieved Chunk #{index})"

        if label not in seen:
            seen.add(label)
            sources.append(label)

    return sources
