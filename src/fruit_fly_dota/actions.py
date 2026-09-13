from enum import IntEnum

class Action(IntEnum):
    WAIT = 0
    LEFT = 1
    RIGHT = 2
    ATTACK = 3

def validate(action):
    if isinstance(action, bool) or not isinstance(action, (int, Action)):
        raise ValueError("Action must be an integer")
    return Action(action)
