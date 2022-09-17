import sys
from collections import Counter
from dataclasses import dataclass
from io import IOBase
from typing import NewType
import re

import w3g

Login = NewType('Login', str)
PlayerID = NewType('PlayerID', int)


@dataclass
class Player:
    login: Login
    apm: float


@dataclass
class AttachmentProcessingResult:
    players: list[Player]
    winner: Login | None
    replay_length: str
    id: int

    def formatted(self) -> str:
        max_login_length = max(max([len(p.login) for p in self.players]), 5)
        stats_header = f'|%{max_login_length}s|  APM|\n|{"-" * max_login_length}|-----|\n' % "Игрок"
        formatted_stats = '\n'.join(f'|%{max_login_length}s|{p.apm:5.2f}|' % p.login for p in self.players)
        return (f' Игра номер {self.id} длительностью {self.replay_length}, '
                f'победитель {self.winner if self.winner is not None else "неизвестен"}. '
                f'Статистика:\n```{stats_header}{formatted_stats}```')


class ReplayFileProcessing:
    async def process(self, file: IOBase) -> AttachmentProcessingResult | None:
        replay = w3g.File(file)
        if map_name_re.search(replay.mapname) is None:
            return None

        raw_players: list[w3g.Player] = replay.players
        apm = self.apm(replay)
        return AttachmentProcessingResult(
            players=[Player(
                p.name,
                apm[p.id],
            ) for p in raw_players],
            winner=self.winner(replay),
            replay_length=format_clock(replay.clock),
            id=int.from_bytes(replay.random_seed, sys.byteorder),
        )

    @staticmethod
    def winner(replay: w3g.File) -> Login | None:
        try:
            return Login(replay.player_name(replay.winner()))
        except (RuntimeError, IndexError):
            return None

    def apm(self, replay: w3g.File) -> dict[PlayerID, float]:
        minutes = replay.clock / (60 * 1000.0)
        events: list[w3g.Action] = replay.events
        count = Counter(e.player_id for e in events if e.apm)
        return {player_id: count / minutes for player_id, count in count.items()}


def format_clock(clock: int) -> str:
    clock //= 1000
    hours = clock // HOUR
    clock %= HOUR
    minutes = clock // MINUTE
    seconds = clock % MINUTE
    return f'{(str(hours) + ":") if hours else ""}{minutes}:{seconds}'


HOUR = 3600
MINUTE = 60

map_name_re = re.compile(r'Survival ?Chaos')
