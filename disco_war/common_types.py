from typing import NewType


GameName = NewType('Game', str)
Login = NewType('Login', str)
PlayerID = NewType('PlayerID', int)
GameID = NewType('GameID', int)
GroupDescriptor = NewType('GroupDescriptor', frozenset[Login])


SURVIVAL_CHAOS = GameName('SurvivalChaos')
