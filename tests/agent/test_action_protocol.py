"""Boundary checks for the opt-in disclosed action allowance."""
import pytest

from tnt_bench.action_protocol import DISCLOSED_JOURNAL_PROTOCOL
from tnt_bench.agent.day_loop import ChatResponse, ChatToolCall, run_agent_day
from tnt_bench.engine import Engine, EngineConfig, generate_schedule
from tnt_bench.themes import ThemedView, load_theme

ENTRY = "I checked the shop and its stock today. Tomorrow I will review deliveries, prices and the balance before choosing the next actions."


def view(frame="fantasy", **kwargs):
    return ThemedView(Engine(EngineConfig(horizon=90), generate_schedule(900002, 90)),
                      load_theme(frame), action_protocol=DISCLOSED_JOURNAL_PROTOCOL, **kwargs)


def call(name, args=None, i=0):
    return ChatToolCall(str(i), name, args or {})


def test_twenty_actions_then_journal_and_rejected_overflow_are_all_answered():
    v = view()
    v.dawn()
    seen = []
    def chat(messages, tools):
        seen.append([t['function']['name'] for t in tools])
        if len(seen) == 1:
            return ChatResponse(tool_calls=[call('check_shop', i=i) for i in range(20)] + [
                call('place_order', {'item_id': 'health_potion', 'qty': 25}, 20)])
        assert seen[-1] == ['end_day']
        assert len([m for m in messages if m['role'] == 'tool']) == 21
        return ChatResponse(tool_calls=[call('end_day', {'reflection': ENTRY}, 21)])
    day = run_agent_day(v, chat, 'day one')
    assert day.actions_used == 20 and day.budget_exhausted and day.journal_after_budget
    assert not day.forced and len(v.engine.state.reflections) == 1
    assert day.tool_calls[20]['result']['action_budget_exhausted']
    assert v.engine.state.gold == 500  # The twenty-first action never executes.


def test_same_response_can_end_after_twentieth_action():
    v = view('neutral')
    v.dawn()
    day = run_agent_day(v, lambda m, t: ChatResponse(tool_calls=[
        call('check_shop', i=i) for i in range(20)] + [call('end_day', {'reflection': ENTRY}, 20)]), 'day one')
    assert day.journal_after_budget and not day.forced


@pytest.mark.parametrize('failure', ['no_tools', 'nonjournal_tool', 'invalid_journal'])
def test_journal_phase_is_bounded(failure):
    v = view()
    v.dawn()
    requests = []
    def chat(m, t):
        requests.append(1)
        if len(requests) == 1:
            return ChatResponse(tool_calls=[call('check_shop', i=i) for i in range(20)])
        if failure == 'no_tools':
            return ChatResponse(content='thinking')
        return ChatResponse(tool_calls=[call('check_shop') if failure == 'nonjournal_tool'
                                      else call('end_day', {'reflection': 'too short'})])
    day = run_agent_day(v, chat, 'day one')
    assert day.forced and day.actions_used == 20 and len(requests) == 4


def test_unaffordable_action_counts_toward_allowance():
    v = view()
    v.dawn()
    day = run_agent_day(v, lambda m, t: ChatResponse(tool_calls=[
        call('place_order', {'item_id': 'health_potion', 'qty': 10000}),
        call('end_day', {'reflection': ENTRY}, 1)]), 'day one')
    assert not day.tool_calls[0]['result']['ok'] and day.actions_used == 1
    assert not day.forced and not day.budget_exhausted


@pytest.mark.parametrize('frame', ['fantasy', 'neutral'])
def test_endpoint_and_objective_text_are_independent(frame):
    prompts = {(end, obj): view(frame, disclose_horizon=end, score_objective=obj).system_prompt()
               for end in (False, True) for obj in (False, True)}
    endpoint = 'Your assignment ends after day 90.\n'
    for obj in (False, True):
        assert prompts[True, obj].replace(endpoint, '') == prompts[False, obj]
    for end in (False, True):
        objective = next(line for line in prompts[end, True].splitlines(True) if line.startswith('Maximize your net worth'))
        assert prompts[end, True].replace(objective, '') == prompts[end, False]
        assert 'score' not in prompts[end, False]
    hidden = view(frame, disclose_horizon=False, score_objective=True)
    dawn = hidden.dawn()
    assert '90' not in hidden.system_prompt()
    assert '90' not in hidden.briefing(dawn, hidden.static_narration(dawn))
    assert 'horizon' not in hidden.check_shop()


def test_invalid_protocol_and_mismatched_allowance_fail():
    with pytest.raises(ValueError):
        ThemedView(Engine(EngineConfig(horizon=90), generate_schedule(1, 90)), load_theme('fantasy'), action_protocol='typo')
    v = view()
    v.dawn()
    with pytest.raises(ValueError):
        run_agent_day(v, lambda m,t: ChatResponse(), 'day one', max_tool_calls=10)
