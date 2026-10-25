"""Small markdown helpers: frontmatter, sections, and placeholder-aware content checks."""
import re

COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
TABLE_SEPARATOR = re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$')
EMPTY_LABEL = re.compile(r'^\s*[-*]\s*[^:]{1,80}:\s*$')
PLACEHOLDER_ID = re.compile(r'^(REQ|QA|EVD|DEC|FEAT|TEST)-XXXX$')
NOT_APPLICABLE = re.compile(r'^\s*not applicable\s*:\s*(\S.*)$', re.IGNORECASE)


def strip_comments(text):
    return COMMENT.sub('', text)


def parse_frontmatter(text):
    """Parse the simple `key: value` / `key: [a, b]` frontmatter used by skills. Returns (meta, body)."""
    if not text.startswith('---\n'):
        return {}, text
    end = text.find('\n---', 4)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, sep, value = line.partition(':')
        if not sep:
            raise ValueError(f'invalid frontmatter line: {line!r}')
        value = value.strip()
        if value.startswith('[') and value.endswith(']'):
            meta[key.strip()] = [item.strip() for item in value[1:-1].split(',') if item.strip()]
        elif value in ('true', 'false'):
            meta[key.strip()] = value == 'true'
        else:
            meta[key.strip()] = value
    body_start = text.find('\n', end + 4)
    return meta, text[body_start + 1:] if body_start != -1 else ''


def headings(text):
    return [m.group(2) for m in (HEADING.match(line) for line in strip_comments(text).splitlines()) if m]


def section(text, heading):
    """Return the body under `heading` (case-insensitive) up to the next heading of the same or higher level, or None.
    When several headings match (a `# Requirements` title above a `## Requirements` section), the deepest one wins."""
    lines = strip_comments(text).splitlines()
    wanted = heading.strip().lower()
    matches = [(len(m.group(1)), i) for i, m in enumerate(HEADING.match(line) for line in lines)
               if m and m.group(2).strip().lower() == wanted]
    if not matches:
        return None
    level, start = max(matches, key=lambda match: (match[0], -match[1]))
    body = []
    for following in lines[start + 1:]:
        n = HEADING.match(following)
        if n and len(n.group(1)) <= level:
            break
        body.append(following)
    return '\n'.join(body)


def _row_cells(line):
    return [cell.strip() for cell in line.strip().strip('|').split('|')]


def meaningful_lines(text):
    """Lines that carry recorded content: drops comments, blank lines, empty `- Label:` items,
    table headers and separators, and table rows holding only blanks or placeholder IDs."""
    lines = strip_comments(text).splitlines()
    kept = []
    for i, line in enumerate(lines):
        if not line.strip() or HEADING.match(line) or EMPTY_LABEL.match(line) or TABLE_SEPARATOR.match(line):
            continue
        if line.strip().startswith('|'):
            following = lines[i + 1] if i + 1 < len(lines) else ''
            if TABLE_SEPARATOR.match(following):
                continue
            if all(not cell or PLACEHOLDER_ID.match(cell) for cell in _row_cells(line)):
                continue
        kept.append(line)
    return kept


def not_applicable_reason(text):
    for line in meaningful_lines(text):
        m = NOT_APPLICABLE.match(line)
        if m:
            return m.group(1).strip()
    return None
