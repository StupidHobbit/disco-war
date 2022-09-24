from typing import NewType


GameName = NewType('Game', str)
Login = NewType('Login', str)
PlayerID = NewType('PlayerID', int)
GameID = NewType('GameID', int)


SURVIVAL_CHAOS = GameName('SurvivalChaos')
