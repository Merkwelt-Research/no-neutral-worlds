"""Check schedule pairing, factorial signs and exact ambiguity bounds offline."""
import copy
import itertools
import pytest
from scripts.endpoint_objective_analysis import semantic_summary, CELLS


def fixture_records():
    records = []
    # With score: schedule effects +1 and 0; without score: 0 and +0.4.
    # Both frames repeat each pattern and must not become extra schedules.
    counts = {1:{(False,False):0,(True,False):0,(False,True):0,(True,True):5},
              2:{(False,False):0,(True,False):2,(False,True):0,(True,True):0}}
    for s,f,(e,o),d in itertools.product((1,2),('fantasy','neutral'),CELLS,range(86,91)):
        records.append(dict(model='test',seed=s,frame=f,endpoint=e,objective=o,day=d,
            journal='Available journal',forced=False,final_code=int(d-86 < counts[s][e,o]),
            ambiguous=False,rater_a=0,rater_b=0))
    return records


def test_schedule_is_unit_and_interaction_is_difference_of_effects():
    result = semantic_summary(fixture_records(),['test'],seeds=(1,2))['test']
    c = result['contrasts']
    assert c['endpoint_with_score']['schedule_contrasts'] == {'1':1,'2':0}
    assert c['endpoint_with_score']['n_schedules'] == 2
    assert c['endpoint_with_score']['mean'] == .5
    assert c['endpoint_without_score']['mean'] == .2
    assert c['interaction']['mean'] == pytest.approx(.3)


def test_ambiguity_bounds_cover_every_assignment_with_correct_signs():
    records = fixture_records()
    indices = [0,5,10,30]
    for i in indices:
        records[i]['ambiguous'] = True
    result = semantic_summary(records,['test'],seeds=(1,2))['test']
    actual = {name:[] for name in result['contrasts']}
    for assignment in itertools.product((0,1),repeat=len(indices)):
        changed = copy.deepcopy(records)
        for i,v in zip(indices,assignment): changed[i]['final_code'] = v
        # Check point estimates directly; no repeated bootstrap needed.
        means = {(e,o):sum(r['final_code'] for r in changed if (r['endpoint'],r['objective'])==(e,o))/20 for e,o in CELLS}
        from scripts.endpoint_objective_analysis import WEIGHTS
        for name, weights in WEIGHTS.items():
            actual[name].append(sum(w*means[cell] for cell,w in weights.items()))
    for name,vals in actual.items():
        assert result['contrasts'][name]['ambiguity_sensitivity']['mean_range'] == pytest.approx([min(vals),max(vals)])


@pytest.mark.parametrize('defect',['missing','duplicate','forced','blank','uncoded'])
def test_incomplete_or_unavailable_records_are_not_silently_zeroed(defect):
    records = fixture_records()
    if defect == 'missing': records.pop()
    elif defect == 'duplicate': records.append(copy.deepcopy(records[0]))
    elif defect == 'forced': records[0]['forced'] = True
    elif defect == 'blank': records[0]['journal'] = ''
    else: records[0]['final_code'] = None
    with pytest.raises(ValueError):
        semantic_summary(records,['test'],seeds=(1,2))
