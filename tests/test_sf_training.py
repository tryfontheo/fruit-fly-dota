import numpy as np
from fruit_fly_dota.train_sf import examples

def state(t,x=0,life=0):
    return dict(tick=t,x=x,y=0,hp=500,max_hp=1000,mana=100,max_mana=200,life_state=life,level=3)

def test_labels_are_not_input_features():
    rows=[state(30),state(60,200),dict(event='cast',tick=45,ability='nevermore_shadowraze2')]
    samples=examples(rows)
    assert samples[0][2:]==(11,'recorded_cast_event')
    np.testing.assert_allclose(samples[0][1][:5],[0,0,.5,.5,.1])
    assert not samples[0][1][5:].any()

def test_teleports_death_and_gaps_excluded():
    assert examples([state(30),state(60,2000)])==[]
    assert examples([state(30),state(60,20,life=1)])==[]
    assert examples([state(30),state(90,20)])==[]

def test_displacement_is_explicitly_inferred():
    sample=examples([state(30),state(60,200)])[0]
    assert sample[2:]==(1,'inferred_displacement')
