import numpy as np
from fruit_fly_dota.reinforcement import RewardLearner


def test_reward_changes_previous_action_preference():
    learner=RewardLearner(3,2)
    x=np.array([1.,.2,1.])
    learner.record(x,np.array([.5,.5]),0)
    learner.feedback(1)
    assert learner.logits(x)[0]>learner.logits(x)[1]
    learner.feedback(-2)
    assert learner.logits(x)[0]<learner.logits(x)[1]


def test_disconnected_graph_cannot_learn_bias_and_reset_clears_credit():
    learner=RewardLearner(3,2)
    learner.record(np.array([0.,0.,1.]),np.array([.5,.5]),0)
    learner.feedback(1)
    assert not learner.weights.any()
    learner.record(np.ones(3),np.array([.5,.5]),0)
    learner.reset_episode();learner.feedback(1)
    assert not learner.weights.any()
