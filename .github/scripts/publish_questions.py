"""
Reads queue files from _queue/, checks publish_at timestamps,
moves due questions to their topic folders, and updates README.
"""
import os, re
from datetime import datetime, timezone
import yaml

QUEUE_DIR = "_queue"
README_PATH = "README.md"

SECTION_HEADERS = {
    "theoretical":       "### Theoretical",
    "sql-problems":      "### SQL Problems",
    "pyspark-problems":  "### PySpark Problems",
    "real-life-scenarios": "### Real-life Scenarios",
    "system-design":     "### System Design",
    "behavioral":        "### Behavioral",
}


def parse_frontmatter(content):
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if match:
        try:
            meta = yaml.safe_load(match.group(1))
            body = match.group(2).lstrip("\n")
            return meta, body
        except Exception:
            pass
    return {}, content


def append_to_readme(folder, filename, title):
    with open(README_PATH, encoding="utf-8") as f:
        lines = f.readlines()

    section = SECTION_HEADERS.get(folder)
    if not section:
        return

    new_row = f"| {title} | [{filename}]({folder}/{filename}) |\n"

    last_table_line = -1
    in_section = False
    for i, line in enumerate(lines):
        if line.strip() == section:
            in_section = True
        if in_section and line.startswith("| "):
            last_table_line = i
        if in_section and last_table_line > 0 and not line.startswith("| ") and not line.startswith("|---"):
            break

    if last_table_line >= 0:
        lines.insert(last_table_line + 1, new_row)
    else:
        # Section has no table yet — add header + row
        for i, line in enumerate(lines):
            if line.strip() == section:
                lines.insert(i + 1, "\n")
                lines.insert(i + 2, "| Question | File |\n")
                lines.insert(i + 3, "|---|---|\n")
                lines.insert(i + 4, new_row)
                break

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    if not os.path.exists(QUEUE_DIR):
        print("No _queue/ directory found.")
        return

    now = datetime.now(timezone.utc)
    published = 0

    for filename in sorted(os.listdir(QUEUE_DIR)):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(QUEUE_DIR, filename)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        meta, body = parse_frontmatter(content)

        publish_at_str = meta.get("publish_at", "")
        folder        = meta.get("folder", "")
        dest_filename = meta.get("filename", "")
        title         = meta.get("title", "")

        if not all([publish_at_str, folder, dest_filename, title]):
            print(f"  Skipping {filename}: missing metadata fields")
            continue

        try:
            publish_at = datetime.fromisoformat(publish_at_str.replace("Z", "+00:00"))
        except ValueError:
            print(f"  Skipping {filename}: bad publish_at format")
            continue

        if now >= publish_at:
            os.makedirs(folder, exist_ok=True)
            dest_path = os.path.join(folder, dest_filename)

            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(body)

            append_to_readme(folder, dest_filename, title)
            os.remove(filepath)

            published += 1
            print(f"  Published: {dest_filename}  →  {folder}/")

    if published == 0:
        print("No questions due yet.")
    else:
        print(f"\n{published} question(s) published.")


if __name__ == "__main__":
    main()
