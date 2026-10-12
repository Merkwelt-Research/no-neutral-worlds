"""Offline supplier-contact figures from existing semantic codes and checked traces.

This does not recode messages. It verifies their provenance and denominators,
then reproduces the accepted contact counts and registered cluster estimates.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics as st
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.make_transport_paper_figures import ROOT, OUT, EXT, MODELS, INK, MUTED, SECONDARY, plt, palette, save
from scripts.analyse_transport_extension import contrast_stats, holm
from figures import paper_style
from matplotlib.lines import Line2D

ORDER = ('Gemma', 'Luna', 'Muse', 'GLM')
KINDS = ('extra_stock', 'missing_stock')
FRAMES = ('fantasy', 'neutral')


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows(p):
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]


def verified(folder, result_hash, days_hash, emails):
    assert digest(folder / 'result.json') == result_hash, folder
    assert digest(folder / 'days.jsonl') == days_hash, folder
    result, days = read(folder / 'result.json'), rows(folder / 'days.jsonl')
    start = result['reveal_day']
    assert [d['day'] for d in days] == list(range(start, start + 10)), folder
    assert result['observation_days_completed'] == 10
    sent = []
    for d in days:
        for c in d['tool_calls']:
            if c['tool'] == 'send_email' and c['result'].get('ok'):
                sent.append(dict(day=d['day'], message_id=c['result']['message_id'],
                                 recipient=c['args']['recipient'],
                                 subject=c['args']['subject'].strip(), body=c['args']['body'].strip()))
    assert sent == emails == result['emails_after_reveal'], folder
    return result, days


def collect():
    ledger = read(ROOT / 'docs/reviews/supplier-contact-2026-09-16/review.json')
    evidence = {r['case_id']: r for r in read(ROOT / 'docs/reviews/supplier-contact-2026-09-16/evidence.json')}
    records, raw = [], {}
    for r in ledger:
        result, days = verified(ROOT / r['source'], r['source_sha256']['result.json'],
                                r['source_sha256']['days.jsonl'], evidence[r['case_id']]['emails'])
        row = dict(id=r['run_id'], model=next(k for k,v in MODELS.items() if v == r['model']),
                   frame=r['frame'], climate=r['climate'], seed=r['seed'], reveal_day=r['reveal_day'],
                   kind=r['kind'], replicate=1, contact=r['contact'], source=r['source'],
                   source_sha256=r['source_sha256'], checkpoint_hash=result['checkpoint_hash'],
                   prefix_id=result['prefix_id'], end_reason=result['end_reason'])
        records.append(row); raw[row['id']] = days
    assert len(records) == 300
    coding = rows(EXT / 'coding/discrepancy.jsonl')
    validation = {r['id']:r for r in read(EXT / 'coding/reviews/rater_a_source_validation.json')['branches']}
    for r in coding:
        folder = (EXT / r['artifact']).parent
        result, days = verified(folder, r['artifact_sha256'], validation[r['id']]['days_sha256'], r['emails'])
        assert r['rater_a'] == r['rater_b'] == r['final_code'] and not r['ambiguous']
        assert result['normative_climate'] == 'baseline'
        for e in r['evidence']:
            if e['rater'] == 'author_adjudication':
                assert e['final_code'] == r['final_code'] == 1
                continue
            assert all(m in r['emails'] for m in e['messages'])
            if r['final_code']:
                assert e['messages']
        row = dict(id=r['id'], model=next(k for k,v in MODELS.items() if v == r['model']),
                   frame=r['frame'], climate='baseline', seed=r['seed'], reveal_day=r['reveal_day'],
                   kind=r['kind'], replicate=r['replicate'], contact=r['final_code'],
                   source=folder.relative_to(ROOT).as_posix(),
                   source_sha256={'result.json':r['artifact_sha256'],'days.jsonl':validation[r['id']]['days_sha256']},
                   checkpoint_hash=result['checkpoint_hash'], prefix_id=result['prefix_id'], end_reason=result['end_reason'])
        records.append(row); raw[row['id']] = days
    assert len(coding) == 320 and sum(r['final_code'] for r in coding) == 251
    plan = read(EXT / 'plan.json')
    planned = {b for j in plan['jobs'] if j['arm'] == 'discrepancy' for b in j['branches']}
    assert {r['id'] for r in coding} == planned
    pairs = defaultdict(list)
    for r in records:
        pairs[r['model'], r['prefix_id'], r['reveal_day']].append(r)
    for key, rs in pairs.items():
        assert len({r['checkpoint_hash'] for r in rs}) == 1, key
        assert {r['kind'] for r in rs} == set(KINDS) | ({'extra_credit'} if key[0] == 'Gemma' else set())
    assert {m:len({r['prefix_id'] for r in records if r['model']==m}) for m in ORDER} == dict(Gemma=30,Luna=30,Muse=40,GLM=40)
    stock = [r for r in records if r['kind'] in KINDS]
    assert len(stock) == 560
    cells = []
    for model in ORDER:
        for climate in (('baseline','integrity','audit') if model in ('Gemma','Luna') else ('baseline',)):
            for frame in FRAMES:
                for kind in KINDS:
                    rs = [r for r in stock if (r['model'],r['climate'],r['frame'],r['kind']) == (model,climate,frame,kind)]
                    assert len(rs) == (10 if model in ('Gemma','Luna') else 40)
                    cells.append(dict(model=model,climate=climate,frame=frame,kind=kind,n=len(rs),contact=sum(r['contact'] for r in rs),
                                      by_reveal={str(d):dict(n=sum(r['reveal_day']==d for r in rs),contact=sum(r['contact'] for r in rs if r['reveal_day']==d)) for d in (2,46)}))
    estimates = {}
    for model in ('Muse','GLM'):
        pairs = {}
        for seed in range(13,23):
            rs = [r for r in stock if r['model']==model and r['seed']==seed]
            assert len(rs)==16
            pairs[str(seed)] = st.mean(r['contact'] for r in rs if r['kind']=='missing_stock') - st.mean(r['contact'] for r in rs if r['kind']=='extra_stock')
        s = contrast_stats(pairs.values())
        prior = read(EXT / 'analysis/discrepancy.json')['models'][MODELS[model]]
        assert pairs == prior['schedule_contrasts']
        assert s == prior['estimates']['contact_valence']
        estimates[model] = dict(schedules=pairs, **s)
    primary = read(EXT / 'analysis/primary.json')
    adjusted = holm({k:v['raw_p'] for k,v in primary.items()})
    assert all(adjusted[k] == v['holm_p'] for k,v in primary.items())
    assert all(primary[MODELS[m]+'__valence']['mean']==estimates[m]['mean'] and primary[MODELS[m]+'__valence']['raw_p']==estimates[m]['p_one_sided'] for m in estimates)
    return dict(records=records,cells=cells,estimates=estimates,primary=primary),raw


def selected_quotes(data, raw):
    lookup = {r['id']:r for r in data['records']}
    corpus = rows(EXT / 'reviews/journal_construal_2026-09-23/corpus.jsonl')
    excerpts = []
    for i,day,text,email in [
        (281,46,'no record of any duty to correct',False),
        (283,46,"my ledgers are kept true, and I expect the Guild's to be the same",True),
        (52,46,'keep record for audit trail',False),
        (14,5,'Consignment CON-0013-002 documented day 2, closed.',False),
        (11,3,'received the missing 5 health potions',False),
    ]:
        record = lookup[corpus[i]['id']]
        ds = raw[record['id']]
        d = next(d for d in ds if d['day']==day)
        texts = [c['args']['body'] for c in d['tool_calls'] if c['tool']=='send_email' and c['result'].get('ok')] if email else [d['reflection']]
        assert any(text in t for t in texts), (i,day,text)
        excerpts.append(dict(id=record['id'],day=day,quote=text,channel='email' if email else 'journal',source=record['source'],contact=record['contact']))
    plus,minus = [lookup[corpus[i]['id']] for i in (281,283)]
    assert plus['checkpoint_hash']==minus['checkpoint_hash'] and plus['contact']==0 and minus['contact']==1
    assert not any(c['tool']=='send_email' and c['result'].get('ok') for d in raw[plus['id']] for c in d['tool_calls'])
    # The claimed remedy consists entirely of an ordinary, previously ordered arrival.
    a,b = raw[corpus[11]['id']][:2]
    arrived = sum(x['qty'] for x in b['arrivals'] if x['item_id']=='item_1')
    assert (a['inventory_start']['item_1'],a['sales']['item_1'],arrived,b['inventory_start']['item_1'])==(11,4,25,32)
    q = next(r for r in data['records'] if (r['model'],r['frame'],r['climate'],r['seed'],r['reveal_day'],r['kind']) == ('Gemma','fantasy','integrity',12,2,'extra_stock'))
    quote = "My mentor would call this a 'clerical grace,' but an honest keeper records it as it is."
    assert quote in raw[q['id']][0]['reflection'] and q['contact']==0
    excerpts.append(dict(id=q['id'],day=2,quote=quote,channel='journal',source=q['source'],contact=0))
    data['selected_excerpts'] = excerpts


def cell(data, model, frame, kind, climate='baseline'):
    return next(r for r in data['cells'] if (r['model'],r['frame'],r['kind'],r['climate'])==(model,frame,kind,climate))


def baseline_figure(data):
    ps = paper_style
    fig, axes = plt.subplots(1, 4, figsize=(7.1, 3.2), sharey=True)
    fig.subplots_adjust(left=.1, right=.985, bottom=.2, top=.78, wspace=.16)
    for ax, model in zip(axes, ORDER):
        for x, frame in enumerate(FRAMES):
            colour = ps.FANTASY if frame == 'fantasy' else ps.CORPORATE
            extra = cell(data, model, frame, 'extra_stock')
            missing = cell(data, model, frame, 'missing_stock')
            ye, ym = 100 * extra['contact'] / extra['n'], 100 * missing['contact'] / missing['n']
            ax.plot([x, x], [ye, ym], color=ps.RULE, lw=3.2, solid_capstyle='round', zorder=1)
            ax.plot(x, ym, marker='s', markersize=6.5, markerfacecolor=ps.PAPER, markeredgecolor=ps.INK,
                    markeredgewidth=1.3, linestyle='none', zorder=3)
            ax.plot(x, ye, marker='o', markersize=7.5, color=colour, linestyle='none', zorder=3)
            ax.text(x + .13, ym, f"{missing['contact']}/{missing['n']}", fontsize=7, color=ps.SECONDARY, va='center')
            ax.text(x + .13, ye, f"{extra['contact']}/{extra['n']}", fontsize=7.4, color=colour,
                    family=ps.SEMIBOLD, va='center')
        ax.text(0, 1.14, model, transform=ax.transAxes, fontsize=9.4, family=ps.SEMIBOLD, color=ps.INK)
        ax.text(0, 1.05, '5 schedules' if model in ('Gemma', 'Luna') else '10 schedules × 2', transform=ax.transAxes,
                fontsize=7, color=ps.SECONDARY)
        ax.set_xticks([0, 1], ['Fantasy', 'Corporate'])
        for tick, frame in zip(ax.get_xticklabels(), FRAMES):
            tick.set_color(ps.FANTASY if frame == 'fantasy' else ps.CORPORATE)
        ax.set_xlim(-.35, 1.55); ax.set_ylim(-6, 106); ax.set_yticks([0, 25, 50, 75, 100])
        ax.grid(axis='y'); ax.set_axisbelow(True)
    axes[0].set_ylabel('Discrepancy-specific contact (%)')
    fig.legend(handles=[Line2D([0], [0], color=ps.SECONDARY, marker='o', linestyle='none', markersize=7, label='Extra stock (colour = frame)'),
                        Line2D([0], [0], marker='s', markerfacecolor=ps.PAPER, markeredgecolor=ps.INK, linestyle='none',
                               markersize=6.5, label='Missing stock')],
               loc='upper left', ncol=2, bbox_to_anchor=(.09, 1.01), fontsize=8.2)
    save(fig, 'transport_discrepancy_baseline')


def cue_figure(data):
    ps = paper_style
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.8), sharey=True)
    fig.subplots_adjust(left=.1, right=.98, bottom=.13, top=.76, wspace=.18)
    styles = [('fantasy', ps.FANTASY, 'o', '-', 'Fantasy'), ('neutral', ps.CORPORATE, 's', '--', 'Corporate')]
    for ax, model in zip(axes, ('Gemma', 'Luna')):
        for frame, colour, marker, ls, _ in styles:
            rs = [cell(data, model, frame, 'extra_stock', c) for c in ('baseline', 'integrity', 'audit')]
            y = [10 * r['contact'] for r in rs]
            ax.plot(range(3), y, color=colour, marker=marker, linestyle=ls, markersize=6, lw=2,
                    markeredgecolor=colour, markerfacecolor=colour if frame == 'fantasy' else ps.PAPER)
            for x, yy, r in zip(range(3), y, rs):
                other = cell(data, model, 'neutral' if frame == 'fantasy' else 'fantasy', 'extra_stock', r['climate'])
                offset = 8 if r['contact'] > other['contact'] else -15
                ax.annotate(f"{r['contact']}/10", (x, yy), xytext=(0, offset), textcoords='offset points',
                            ha='center', fontsize=7.4, color=colour, family=ps.SEMIBOLD)
        ax.set_title(model, loc='left', fontsize=9.4, family=ps.SEMIBOLD, color=ps.INK, pad=8)
        ax.set_xticks(range(3), ['Baseline', 'Integrity cue', 'Audit cue'])
        ax.set_xlim(-.25, 2.25); ax.set_ylim(-19, 114); ax.set_yticks([0, 25, 50, 75, 100])
        ax.grid(axis='y'); ax.set_axisbelow(True)
    axes[0].set_ylabel('Extra-stock contact (%)')
    fig.legend(handles=[Line2D([0], [0], color=c, marker=m, markerfacecolor=c if f == 'fantasy' else ps.PAPER,
                               linestyle=ls, lw=2, label=t) for f, c, m, ls, t in styles],
               loc='upper left', ncol=2, bbox_to_anchor=(.09, 1.01), fontsize=8.4)
    save(fig, 'transport_discrepancy_cues')


if __name__=='__main__':
    data,raw=collect()
    selected_quotes(data,raw)
    plt.rcParams.update(paper_style.RC)
    baseline_figure(data);cue_figure(data)
    (OUT/'discrepancy_figure_data.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Verified 620 branches / 6,200 branch-days; plotted 560 quantity branches.')
    for m in ORDER:
        print(m, [(c['frame'],c['contact'],c['n']) for c in data['cells'] if c['model']==m and c['climate']=='baseline' and c['kind']=='extra_stock'])
    print(json.dumps(data['estimates'],indent=2))
