import copy
import numpy as np
import torch
from scipy.sparse import csr_matrix
from fruit_fly_dota.full_neural import FullReservoir
from fruit_fly_dota.recurrent import SharedPPO
from fruit_fly_dota.shared import SharedController
from fruit_fly_dota.schema import OBS_SIZE,ACTION_COUNT,SCHEMA

def brain():
    return FullReservoir(csr_matrix(([1.],([1],[0])),shape=(2,2)),[0],[1],input_size=OBS_SIZE)

def packet(agent='0',seq=0):
    return dict(env='test',agent=agent,session='game1',seq=seq,obs=[.1]*OBS_SIZE,legal=[1]*ACTION_COUNT)

def test_agents_share_weights_but_not_memory():
    learner=SharedPPO(64,ACTION_COUNT,rollout=16)
    c=SharedController(brain(),learner)
    c.step(packet('0'));h=learner.states['test/0'].clone();state=c.streams['test/0']['brain'].state.copy()
    c.step(packet('1'))
    torch.testing.assert_close(h,learner.states['test/0'])
    np.testing.assert_array_equal(state,c.streams['test/0']['brain'].state)
    assert c.streams['test/0']['brain'].w is c.streams['test/1']['brain'].w
    assert not np.shares_memory(c.streams['test/0']['brain'].state,c.streams['test/1']['brain'].state)

def test_pooled_experience_updates_weights_and_terminal_is_idempotent(tmp_path):
    learner=SharedPPO(64,ACTION_COUNT,rollout=8)
    c=SharedController(brain(),learner)
    for seq in range(6):
        for agent in ('0','1'):
            p=packet(agent,seq);p['reward']=.2 if agent=='0' else -.1;c.step(p)
    assert learner.version>=1 and learner.stats['parameter_change']>0
    p=packet('0',6);p.update(terminal=True,reward=100)
    result=c.step(p);total=learner.total_reward
    assert c.step(p)==result and learner.total_reward==total
    assert 'test/0' not in learner.states
    path=tmp_path/'saved.pt';learner.save(path,SCHEMA)
    restored=SharedPPO(64,ACTION_COUNT);restored.load(path,SCHEMA)
    for a,b in zip(learner.policy.parameters(),restored.policy.parameters()):torch.testing.assert_close(a,b)
    assert restored.version==learner.version

def test_new_lua_modules_compile():
    from pathlib import Path
    from lupa import LuaRuntime
    for name in ('neural_agent','interactions','guide_items'):
        LuaRuntime().execute(Path('dota/live/scripts/vscripts',name+'.lua').read_text(encoding='utf-8'))

def test_failed_order_does_not_receive_credit():
    learner=SharedPPO(64,ACTION_COUNT,rollout=16)
    c=SharedController(brain(),learner)
    c.step(packet())
    p=packet(seq=1);p.update(previous_applied=False,reward=1.)
    c.step(p)
    assert learner.samples==0 and not learner.buffers
    p=packet(seq=2);p.update(previous_applied=True,reward=.5)
    c.step(p)
    assert learner.samples==1


def test_rejected_order_preserves_earlier_learning_and_cuts_credit_trace():
    learner=SharedPPO(64,ACTION_COUNT,rollout=100)
    c=SharedController(brain(),learner)
    c.step(packet(seq=0))
    p=packet(seq=1);p['reward']=1.;c.step(p)
    first=learner.buffers['test/0'][0]
    p=packet(seq=2);p.update(previous_applied=False,reward=100.);c.step(p)
    assert learner.buffers['test/0']==[first]
    assert first['trace_end'] and learner.samples==1
    p=packet(seq=3);p['reward']=2.;c.step(p)
    expected=first['reward']+learner.gamma**first['elapsed']*first['next_value']-first['value']
    learner.update()
    assert abs(first['adv']-expected)<1e-6
    assert learner.stats['samples']==2


def test_delayed_reward_changes_policy_in_correct_direction():
    # Learner plumbing check, not evidence of Dota competence or fly memory.
    learner=SharedPPO(2,2,hidden=8,rollout=32,seed=7)
    x=np.array([1.,0.]);mask=[1,1]
    with torch.no_grad():
        before=learner.policy(torch.tensor(x,dtype=torch.float32)[None],torch.zeros(1,8),torch.tensor([[True,True]]))[0].probs[0,1].item()
    for _ in range(4096):
        a,_=learner.act('probe',x,mask)
        learner.act('probe',x,mask,reward=1. if a==1 else -1.,done=True,elapsed=10.)
    with torch.no_grad():
        after=learner.policy(torch.tensor(x,dtype=torch.float32)[None],torch.zeros(1,8),torch.tensor([[True,True]]))[0].probs[0,1].item()
    assert after>before+.1
