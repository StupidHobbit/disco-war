from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from typing import AsyncContextManager, Protocol

import redis.asyncio as redis

from disco_war.repository import types
from disco_war.common_types import Login, GroupDescriptor, GameName


class RedisContext(AsyncContextManager):
    def __init__(self, r: redis.Redis):
        self.p = r.pipeline()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_value is None:
            await self.p.execute()


@dataclass
class RepositoryContextManager:
    r: redis.Redis

    def start(self) -> RedisContext:
        return RedisContext(self.r)


@dataclass
class RedisKeysManager:
    root: str

    def key(self, k: str) -> str:
        return f'{self.root}:{k}'

    def namespace(self, k: str) -> RedisKeysManager:
        return RedisKeysManager(f'{self.root}:{k}')


class GroupOptions(Protocol):
    group: GroupDescriptor
    game_name: GameName


@dataclass
class RedisIndividualStatsRepository:
    r: redis.Redis
    keys_manager: RedisKeysManager

    async def add_game_played_for_player(self, context: RedisContext, options: types.ChangeIndividualStatsOptions):
        game_keys = self.keys_manager.namespace(options.game_name)
        key = game_keys.key(options.player)
        await context.p.sadd(game_keys.key(INDIVIDUAL_PLAYERS_INDEX_KEY), options.player)
        await context.p.hincrby(key, GAMES_PLAYED_FIELD, options.amount)

    async def add_game_won_for_player(self, context: RedisContext, options: types.ChangeIndividualStatsOptions):
        key = self.keys_manager.namespace(options.game_name).key(options.player)
        await context.p.hincrby(key, GAMES_WON_FIELD, options.amount)

    async def stats(self, context: RedisContext, options: types.AllIndividualStatsOptions) -> list[types.IndividualStats]:
        game_keys = self.keys_manager.namespace(options.game_name)
        players = await self.r.smembers(game_keys.key(INDIVIDUAL_PLAYERS_INDEX_KEY))
        for p in players:
            await context.p.hgetall(game_keys.key(p))
        return [
            self._parse_stats(p, s)
            for p, s in zip(players, await context.p.execute())
        ]

    async def add_game_played_in_group_for_player(self, context: RedisContext, options: types.ChangeIndividualGroupStatsOptions):
        group_namespace = self._get_group_namespace(options)
        key = group_namespace.key(options.player)
        await context.p.hincrby(key, GAMES_PLAYED_FIELD, options.amount)
        await context.p.sadd(group_namespace.key(GROUP_MEMBERS_KEY), options.player)

    async def add_game_won_in_group_for_player(self, context: RedisContext, options: types.ChangeIndividualGroupStatsOptions):
        key = self._get_player_group_stats_key(options)
        await context.p.hincrby(key, GAMES_WON_FIELD, options.amount)

    async def group_stats(self, context: RedisContext, options: types.GroupIndividualStatsOptions):
        group_namespace = self._get_group_namespace(options)
        players = await self.r.smembers(group_namespace.key(GROUP_MEMBERS_KEY))
        for p in players:
            await context.p.hgetall(group_namespace.key(p))
        return [
            self._parse_stats(p, s)
            for p, s in zip(players, await context.p.execute())
        ]

    async def stats_for_player(self, context: RedisContext, options: types.OneIndividualStatsOptions) -> types.IndividualStats | None:
        game_keys = self.keys_manager.namespace(options.game_name)
        raw = await self.r.hgetall(game_keys.key(options.player))
        if raw:
            return self._parse_stats(options.player, raw)
        return None

    async def remove_stats(self, context: RedisContext, options: types.OneIndividualStatsOptions):
        key = self.keys_manager.namespace(options.game_name).key(options.player)
        await context.p.delete(key)

    def _get_player_group_stats_key(self, options: types.ChangeIndividualGroupStatsOptions) -> str:
        group_keys = self._get_group_namespace(options)
        return group_keys.key(options.player)

    def _get_group_namespace(self, options: GroupOptions) -> RedisKeysManager:
        game_keys = self.keys_manager.namespace(options.game_name).namespace(serialize_group(options.group))
        return game_keys.namespace(GROUP_KEY)

    @staticmethod
    def _parse_stats(login: Login, raw_stats: dict) -> types.IndividualStats:
        return types.IndividualStats(
            games_played=int(raw_stats.get(GAMES_PLAYED_FIELD, 0)),
            games_won=int(raw_stats.get(GAMES_WON_FIELD, 0)),
            login=login,
        )


@dataclass
class GamesRepository:
    r: redis.Redis
    keys_manager: RedisKeysManager

    async def add_played_game(self, context: RedisContext, options: types.GameOptions) -> types.AddGameResults:
        key = self.keys_manager.namespace(options.game_name).key(GAMES_INDEX_KEY)
        added = await self.r.sadd(key, options.id)
        status = types.AddGameStatus.ADDED if added else types.AddGameStatus.DUPLICATE
        return types.AddGameResults(status)


@dataclass
class PlayersRepository:
    r: redis.Redis
    keys_manager: RedisKeysManager

    async def add_alias(self, context: RedisContext, options: types.AddPlayerAliasOptions):
        await context.p.hset(
            self.keys_manager.key(ALIASES_KEY),
            options.alias,
            options.login,
        )

    async def normalize_players(self, context: RedisContext, players: Iterable[Login]) -> Iterable[Login | None]:
        return await self.r.hmget(
            self.keys_manager.key(ALIASES_KEY),
            list(players),
        )


def make_redis(
        host: str = os.getenv('REDIS_HOST', 'localhost'),
        port: int = int(os.getenv('REDIS_PORT', 6379)),
        password: str | None = os.getenv('REDIS_PASSWORD'),
        cert_path: str | None = os.getenv('CERT_PATH'),
) -> redis.Redis:
    return redis.Redis(
        host=host,
        port=port,
        password=password,
        decode_responses=True,
        ssl=cert_path is not None,
        ssl_ca_certs=cert_path,
    )


def serialize_group(group: GroupDescriptor) -> str:
    return ''.join(login[:2] for login in sorted(group))


GROUP_KEY = 'gr'
GROUP_MEMBERS_KEY = 'members'
GAMES_PLAYED_FIELD = 'ga'
GAMES_WON_FIELD = 'gw'
INDIVIDUAL_PLAYERS_INDEX_KEY = '#index'
GAMES_INDEX_KEY = '#index'
ALIASES_KEY = '#aliases'
