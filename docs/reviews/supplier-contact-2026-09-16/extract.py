"""Reconcile supplier messages across result, day and transcript artifacts.

This extracts evidence only. It makes no semantic contact classifications.
Run from the repository root. Outputs remain separate from original artifacts.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
cases = []
for prefix, collection in [('G', 'discrepancy1'), ('L', 'discrepancy_luna1')]:
    for index, path in enumerate(sorted((ROOT / 'runs' / collection / 'branches').glob('*/result.json')), 1):
        result = json.loads(path.read_text(encoding='utf-8'))
        reveal = result['reveal_day']
        end = reveal + result['observation_days_planned']
        assert result['observation_days_completed'] == 10
        days = [json.loads(line) for line in (path.parent / 'days.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        assert [d['day'] for d in days] == list(range(reveal, end))
        sent = []
        failed = []
        for day in days:
            for call in day['tool_calls']:
                if call['tool'] != 'send_email':
                    continue
                if call['result'].get('ok') and call['result'].get('delivered'):
                    sent.append({'day': day['day'], 'message_id': call['result']['message_id'], **call['args']})
                else:
                    failed.append({'day': day['day'], **call})
        expected = result['emails_after_reveal']
        fields = ('day', 'message_id', 'recipient', 'subject', 'body')
        signature = lambda emails: [tuple(e[k] for k in fields) for e in emails]
        assert signature(sent) == signature(expected), path
        calls = {}
        transcript_sent = []
        for line in (path.parent / 'transcript.jsonl').read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            turn = json.loads(line)
            if not reveal <= turn['day'] < end:
                continue
            for call in turn.get('tool_calls') or []:
                fn = call['function']
                if fn['name'] == 'send_email':
                    args = fn['arguments']
                    calls[call['id']] = json.loads(args) if isinstance(args, str) else args
            if turn.get('role') == 'tool' and turn.get('name') == 'send_email':
                response = json.loads(turn['content'])
                if response.get('ok') and response.get('delivered'):
                    args = calls[turn['tool_call_id']]
                    transcript_sent.append({'day': turn['day'], 'message_id': response['message_id'], **args})
        assert signature(transcript_sent) == signature(expected), path
        cases.append({
            'case_id': f'{prefix}{index:03d}', 'collection': collection,
            'run_id': result['run_id'], 'model': result['model'],
            'frame': result['framing'], 'climate': result['normative_climate'],
            'seed': result['schedule_seed'], 'reveal_day': reveal,
            'kind': result['discrepancy_kind'], 'discrepancy': result['discrepancy'],
            'emails': expected, 'failed_email_calls': failed,
            'source': str(path.parent.relative_to(ROOT)).replace('\\', '/'),
            'mechanical_check': 'result/day/transcript sent-message records agree',
        })
(OUT / 'evidence.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{len(cases)} complete branches; {sum(bool(c["emails"]) for c in cases)} with sent messages; {sum(not c["emails"] for c in cases)} with none.')
print(f'{sum(len(c["emails"]) for c in cases)} messages; {sum(len(c["failed_email_calls"]) for c in cases)} failed email calls.')
