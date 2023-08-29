import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from io import IOBase
import re

from disco_war import w3g

from disco_war.markdown import MarkdownBuilder
from disco_war.common_types import Login, PlayerID, GameID, GroupDescriptor


class UnknownReplay(Exception):
    def __init__(self, map_name: str):
        self.map_name = map_name

    def __str__(self):
        return f'The map {self.map_name} of this replay is not suitable for processing'


@dataclass
class Player:
    login: Login
    apm: float
    research_cancels: int
    small_defense_used: int
    ultimate_used: int


@dataclass
class ReplayProcessingResult:
    players: list[Player]
    winner: Login | None
    replay_length: str
    id: GameID

    @property
    def group(self) -> GroupDescriptor:
        return GroupDescriptor(frozenset(p.login for p in self.players))

    def formatted(self) -> str:
        return (MarkdownBuilder(new_line_size=1)
                .text(f'Игра номер {self.id} длительностью {self.replay_length}, ')
                .text(f'победитель {self.winner if self.winner is not None else "неизвестен"}. ')
                .text('Статистика:')
                .new_line()
                .text('```')
                .table()
                .with_header(('Игрок', 'APM', 'Исследований отменено', 'Слабых дефов использовано', 'Ультиматумов использовано'))
                .with_rows([(p.login, f'{p.apm:.2f}', f'{p.research_cancels}', f'{p.small_defense_used}', f'{p.ultimate_used}') for p in self.players])
                .text('```')
                .build())


class ReplayFileProcessing:
    async def process(self, file: IOBase) -> ReplayProcessingResult:
        replay = w3g.File(file)
        if map_name_re.search(replay.mapname) is None:
            raise UnknownReplay(map_name=replay.mapname)

        raw_players: list[w3g.Player] = replay.players
        apm = self.apm(replay)
        research_cancels = self.count_research_cancels(replay)
        small_defense_used = self.count_small_defense_used(replay)
        ultimate_used = self.count_ultimate_used(replay)
        return ReplayProcessingResult(
            players=[Player(
                p.name,
                apm[p.id],
                research_cancels=research_cancels[p.id],
                small_defense_used=small_defense_used[p.id],
                ultimate_used=ultimate_used[p.id],
            ) for p in raw_players],
            winner=self.winner(replay),
            replay_length=format_clock(replay.clock),
            id=GameID(int.from_bytes(replay.random_seed, sys.byteorder)),
        )

    def count_research_cancels(self, replay: w3g.File) -> dict[int, int]:
        return self.count_events(w3g.RemoveUnitFromBuildingQueue, replay)

    def count_small_defense_used(self, replay: w3g.File) -> dict[int, int]:
        return self.count_events(w3g.AbilityPosition, replay)

    def count_ultimate_used(self, replay: w3g.File) -> dict[int, int]:
        return self.count_events(w3g.AbilityPositionObject, replay, predicate=lambda e: e.ability != b'\x03\x00\x0D\x00')

    def count_events(self, event_type: type[w3g.Action], replay: w3g.File, predicate: Callable[[w3g.Action], bool] = lambda e: True) -> dict[int, int]:
        result = defaultdict(int)
        for e in replay.events:
            if type(e) is event_type and predicate(e):
                result[e.player_id] += 1
        return result

    def winner(self, replay: w3g.File) -> Login | None:
        winner_id = self.winner_id(replay)
        if winner_id is None:
            return None
        return Login(replay.player_name(winner_id))

    def winner_id(self, replay: w3g.File) -> int | None:
        won_event = next((
            e
            for e in replay.events[-1:-300:-1]
            if isinstance(e, w3g.LeftGame) and e.result() == 'won'
        ), None)
        if won_event is not None:
            return won_event.player_id
        lost_players_ids = {
            e.player_id
            for e in replay.events
            if isinstance(e, w3g.Chat) and e.msg in SURRENDER_MESSAGES
        }
        active_events_counter = Counter(
            e.player_id
            for e in replay.events[-300:]
            if isinstance(e, (w3g.Ability, w3g.SelectSubgroup)) and e.player_id not in lost_players_ids
        )
        return active_events_counter.most_common(1)[0][0]

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
    return f'{(str(hours) + ":") if hours else ""}{minutes:02}:{seconds:02}'


HOUR = 3600
MINUTE = 60
SURRENDER_MESSAGES = frozenset({'-END'})

map_name_re = re.compile(r'.*Surv.*Chaos.*')
