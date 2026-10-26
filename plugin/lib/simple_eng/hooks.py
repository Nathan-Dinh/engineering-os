"""Claude Code hook entry points. Each reads the hook's JSON from stdin and prints the hook's output.

- session-start: prints the project context (plain text is added to Claude's context).
- prompt-expansion: records approve/reject events from a slash command the user typed.
  UserPromptExpansion fires only for user-typed commands, not when Claude invokes a skill.
- pre-tool-use: denies direct writes to the decision log and attempts to impersonate the approval hook.

Plugin hooks fire in every repository where the plugin is enabled, so `run` skips projects that never ran init.
"""
import hashlib
import json
import os
import re
import subprocess

from .context import build_context
from .paths import LOG, is_initialized, project_root
from .records import DEC_ID, record_user_decision

COMMAND = re.compile(r'^(?:simple-eng:)?(approve|reject)$')
LOG_NAME = 'decision-log/events.jsonl'
FILE_TOOLS = ('Edit', 'Write', 'MultiEdit', 'NotebookEdit')
IMPERSONATION = re.compile(r'record_user_decision|user-prompt-hook|UserPromptExpansion;|(^|[\s/;&|])simple-eng\s+hook\b|\bsimple_eng/hooks\.py\b')
WRITES = re.compile(r'>|\btee\b|\bsed\b[^|;&]*\s-i|\bperl\b[^|;&]*\s-i|\btruncate\b|\brm\b|\bmv\b|\bcp\b|\bdd\b|'
                    r'\bpython3?\b|\bnode\b|\bruby\b|\bgit\s+(checkout|restore|reset|rm)\b')
FD_REDIRECT = re.compile(r'\d?>&\d|&>\s*/dev/null|\d?>\s*/dev/null')


def _root(payload):
    return project_root(os.environ.get('CLAUDE_PROJECT_DIR') or payload.get('cwd'))


def session_start(payload):
    try:
        return build_context(_root(payload))
    except Exception as exc:  # a broken project must never break session start
        return f'simple-eng: could not build project context ({exc}). Run `simple-eng validate` for details.'


def _git(root, key):
    try:
        out = subprocess.run(['git', '-C', str(root), 'config', key], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ''
    return out.stdout.strip() if out.returncode == 0 else ''


def _block(reason):
    return {'decision': 'block', 'reason': f'simple-eng did not record this: {reason}'}


def prompt_expansion(payload):
    m = COMMAND.match(str(payload.get('command_name', '')))
    if not m or payload.get('expansion_type', 'slash_command') != 'slash_command':
        return None
    if payload.get('command_source') not in (None, 'plugin'):
        return None
    kind = 'approved' if m.group(1) == 'approve' else 'rejected'
    args = str(payload.get('command_args', '')).strip().split(None, 1)
    decision_id = args[0] if args else ''
    note = args[1].strip() if len(args) > 1 else ''
    if not DEC_ID.match(decision_id):
        return _block(f'usage is /simple-eng:{m.group(1)} DEC-#### ' + ('<reason>' if kind == 'rejected' else '[note]'))
    if kind == 'rejected' and not note:
        return _block('a rejection needs a reason, for example /simple-eng:reject DEC-0001 too costly for the MVP')
    root = _root(payload)
    if not is_initialized(root):
        return _block(f'{root} is not a simple-eng project; run /simple-eng:init first')
    email = _git(root, 'user.email')
    if not email:
        return _block('git user.email is not set, so the approver cannot be identified; set it with `git config user.email you@example.com`')
    name = _git(root, 'user.name')
    actor = f'{name} <{email}>' if name else email
    session = re.sub(r'[;\s]', '_', str(payload.get('session_id') or 'unknown'))
    digest = hashlib.sha256(str(payload.get('prompt', '')).encode('utf-8')).hexdigest()
    try:
        event = record_user_decision(root, decision_id=decision_id, kind=kind, note=note, actor=actor,
                                     attestation=f'UserPromptExpansion;session={session};prompt-sha256={digest}')
    except ValueError as exc:
        return _block(str(exc))
    return {'hookSpecificOutput': {
        'hookEventName': 'UserPromptExpansion',
        'additionalContext': (f'simple-eng recorded event {event["event_id"]}: {decision_id} {kind} by {actor} '
                              f'at {event["timestamp"]}, from the slash command the user typed. Written to {LOG}.')}}


def _deny(reason):
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                   'permissionDecisionReason': reason}}


def pre_tool_use(payload):
    tool = payload.get('tool_name', '')
    data = payload.get('tool_input')
    data = data if isinstance(data, dict) else {}
    if tool in FILE_TOOLS:
        path = str(data.get('file_path') or data.get('notebook_path') or '').replace('\\', '/')
        if path == LOG_NAME or path.endswith('/' + LOG_NAME):
            return _deny(f'{LOG_NAME} is written only by `simple-eng add-decision` (proposals and other low-authority events) '
                         'and by the approval hook when the decision owner types /simple-eng:approve. Use `simple-eng add-decision`.')
    elif tool == 'Bash':
        command = str(data.get('command', ''))
        if IMPERSONATION.search(command):
            return _deny('Approval events are recorded only by the simple-eng hook from a command the decision owner types. '
                         'Ask the user to type /simple-eng:approve DEC-#### themselves.')
        if LOG_NAME in command and WRITES.search(FD_REDIRECT.sub('', command)):
            return _deny(f'Direct writes to {LOG_NAME} are blocked. Use `simple-eng add-decision` for proposals; reading the file is fine.')
    elif tool == 'Skill':
        name = str(data.get('skill') or data.get('name') or data.get('command') or '')
        if COMMAND.match(name.lstrip('/')):
            return _deny('Only the decision owner can approve or reject. Ask the user to type /simple-eng:approve DEC-#### themselves.')
    return None


HANDLERS = {'session-start': session_start, 'prompt-expansion': prompt_expansion, 'pre-tool-use': pre_tool_use}
# Runs outside a simple-eng project too, so a typed /simple-eng:approve there is told why nothing was recorded.
ALWAYS_RUN = ('prompt-expansion',)


def run(name, stdin):
    try:
        payload = json.loads(stdin or '{}')
    except ValueError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    if name not in ALWAYS_RUN and not is_initialized(_root(payload)):
        return ''
    result = HANDLERS[name](payload)
    if result is None:
        return ''
    return result if isinstance(result, str) else json.dumps(result)
