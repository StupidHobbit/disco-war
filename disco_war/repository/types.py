from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol, TypeVar, AsyncContextManager

from disco_war.types import Login, GameName, SURVIVAL_CHAOS, GameID

RepositoryContext = TypeVar('RepositoryContext', bound=AsyncContextManager)


class RepositoryContextManager(Protocol[RepositoryContext]):
    def start(self) -> RepositoryContext: ...


@dataclass
class IndividualStats:
    login: Login
    games_played: int
    games_won: int


@dataclass
class ChangeIndividualStatsOptions:
    player: Login
    amount: int = 1
    game_name: GameName = SURVIVAL_CHAOS


@dataclass
class AllIndividualStatsOptions:
    game_name: GameName = SURVIVAL_CHAOS


@dataclass
class OneIndividualStatsOptions:
    player: Login
    game_name: GameName = SURVIVAL_CHAOS


@dataclass
class GameOptions:
    id: GameID
    game_name: GameName = SURVIVAL_CHAOS


@dataclass
class AddPlayerAliasOptions:
    login: Login
    alias: Login


class AddGameStatus(Enum):
    ADDED = auto()
    DUPLICATE = auto()


@dataclass
class AddGameResults:
    status: AddGameStatus


class IndividualStatsRepository(Protocol[RepositoryContext]):
    async def add_game_played_for_player(self, context: RepositoryContext, options: ChangeIndividualStatsOptions): ...
    async def add_game_won_for_player(self, context: RepositoryContext, options: ChangeIndividualStatsOptions): ...
    async def stats(self, context: RepositoryContext, options: AllIndividualStatsOptions) -> list[IndividualStats]: ...
    async def stats_for_player(self, context: RepositoryContext, options: OneIndividualStatsOptions) -> IndividualStats | None: ...
    async def remove_stats(self, context: RepositoryContext, options: OneIndividualStatsOptions): ...


class GamesRepository(Protocol[RepositoryContext]):
    async def add_played_game(self, context: RepositoryContext, options: GameOptions) -> AddGameResults: ...


class PlayersRepository(Protocol[RepositoryContext]):
    async def add_alias(self, context: RepositoryContext, options: AddPlayerAliasOptions): ...
    async def normalize_players(self, context: RepositoryContext, players: Iterable[Login]) -> Iterable[Login | None]: ...
