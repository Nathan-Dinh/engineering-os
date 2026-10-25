"""Static, read-only HTML report of the latest event per decision."""
import html


def render_dashboard(events):
    latest, counts = {}, {}
    for e in events:
        latest[e['decision_id']] = e
        counts[e['event']] = counts.get(e['event'], 0) + 1

    def esc(value):
        return html.escape(str(value), quote=True)

    rows = ''.join(
        '<tr>' + ''.join(f'<td>{esc(v)}</td>' for v in (dec, e.get('title', ''), e['event'], e.get('actor', ''),
                                                          e.get('timestamp', ''), e.get('summary', ''))) + '</tr>'
        for dec, e in sorted(latest.items()))
    count_text = ', '.join(f'{esc(k)}: {v}' for k, v in sorted(counts.items())) or 'No decisions recorded'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Decision Review</title><style>'
            ':root{--bg:#f7f8fa;--fg:#172033;--muted:#566174;--card:#fff;--line:#dce1e8;--head:#eef2f6}'
            '@media (prefers-color-scheme:dark){:root{--bg:#12151b;--fg:#e6e9ef;--muted:#9aa4b5;--card:#1a1e26;--line:#2c3340;--head:#222834}}'
            'body{font:16px system-ui,sans-serif;background:var(--bg);color:var(--fg);max-width:1100px;margin:3rem auto;padding:0 1rem}'
            '.note{color:var(--muted)}.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--line)}'
            'th,td{text-align:left;padding:.8rem;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}'
            'th{background:var(--head)}input{font:inherit;padding:.6rem;width:min(100%,22rem);margin:1rem 0}tr[hidden]{display:none}'
            '</style></head><body><h1>Decision Review</h1><p class="note">Local, read-only snapshot of decision-log/events.jsonl. '
            'Events are not cryptographically authenticated. Approvals cannot be made here.</p>'
            f'<p>{count_text}</p><label for="filter">Filter decisions</label><br>'
            '<input id="filter" placeholder="ID, status, actor, title…"><div class="wrap"><table><thead><tr><th>ID</th><th>Title</th>'
            '<th>Latest event</th><th>Actor</th><th>Timestamp</th><th>Summary</th></tr></thead><tbody>' + rows +
            '</tbody></table></div><script>document.getElementById("filter").addEventListener("input",function(){'
            'const q=this.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))})'
            '</script></body></html>')
