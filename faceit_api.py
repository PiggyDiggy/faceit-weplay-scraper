from asyncio import gather
from aiohttp import ClientSession
from utils import request

base_url = "https://open.faceit.com/data/v4/players"
headers = {
    "accept": "application/json",
    "Authorization": "TOKEN",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
}


async def get_player_info(session: ClientSession, steam_id: str):
    params = {"game": "csgo", "game_player_id": steam_id}
    response = await request(session, base_url, "get", headers, params=params)
    if "errors" in response:
        return f"Профиль Faceit не найден"
    return response


def parse_response(response: dict):
    player_id = response["player_id"]
    nickname = response["nickname"]
    elo = response["games"]["csgo"]["faceit_elo"]
    return player_id, nickname, elo


def parse_missing_players(players: dict):
    missing = {
        steam_id: player
        for steam_id, player in players.items()
        if isinstance(player, str)
    }
    actual = {
        steam_id: player
        for steam_id, player in players.items()
        if isinstance(player, dict)
    }
    return actual, missing


async def get_stats(session: ClientSession, player_id: str):
    url = f"{base_url}/{player_id}/stats/csgo"
    response = await request(session, url, "get", headers)
    stats = response["lifetime"]
    return {
        "Матчей": stats["Matches"],
        "Winrate": stats["Win Rate %"] + "%",
        "Побед": stats["Wins"],
        "K/D": stats["Average K/D Ratio"],
        "HS": stats["Average Headshots %"] + "%",
    }


async def get_stats_for_multiple_players(steam_ids: list):
    async with ClientSession() as session:
        results = await gather(
            *(get_player_info(session, steam_id) for steam_id in steam_ids)
        )
        players = {
            steam_id: result
            for steam_id, result in zip(steam_ids, results)
            if isinstance(result, dict)
        }
        for steam_id, player_info in players.items():
            players[steam_id] = parse_response(player_info)
        stats = await gather(
            *(get_stats(session, player[0]) for player in players.values())
        )
        for i, items in enumerate(players.items()):
            steam_id, player_info = items
            players[steam_id] = {
                "ELO": str(player_info[2]),
                "nickname": player_info[1],
                **stats[i],
            }
        return players
