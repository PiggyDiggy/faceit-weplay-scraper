from utils import request, get_date
from asyncio import gather
from aiohttp import ClientSession
from tokens import steam_api_key

base_url = "https://api.steampowered.com"
key = steam_api_key


async def get_players_summaries(session: ClientSession, steam_ids: list):
    url = f"{base_url}/ISteamUser/GetPlayerSummaries/v0002/"
    params = {"key": key, "steamids": ",".join(steam_ids)}
    response = await request(session, url, "get", params=params)
    return response


async def get_recently_played_games(session: ClientSession, steam_id: str):
    url = f"{base_url}/IPlayerService/GetRecentlyPlayedGames/v0001"
    params = {"key": key, "steamid": steam_id}
    response = await request(session, url, "get", params=params)
    if not isinstance(response, dict):
        response = {"response": {}}
    response.update({"steamid": steam_id})
    return response


async def get_timestamps(session: ClientSession, steam_ids: list):
    response = await get_players_summaries(session, steam_ids)
    players = response["response"]["players"]
    return {
        player["steamid"]: {"Аккаунт создан": get_date(player["timecreated"])}
        for player in players
        if player["communityvisibilitystate"] == 3
    }


def get_playtime(player: dict):
    fallback = {
        "steam_id": player["steamid"],
        "playtime": {
            "Всего часов в CS:GO": "Скрыто",
            "Часов в CS:GO за 2 недели": "Скрыто",
        },
    }

    if player["response"] == {}:
        return fallback

    for game in player["response"]["games"]:
        if game["appid"] == 730:
            recent = game["playtime_2weeks"] / 60
            recent = str(int(recent)) if not recent % 1 else f"{recent:.1f}"
            total = str(game["playtime_forever"] // 60)
            return {
                "steam_id": player["steamid"],
                "playtime": {
                    "Всего часов в CS:GO": total,
                    "Часов в CS:GO за 2 недели": recent,
                },
            }

    return fallback


async def get_accounts_info(steam_ids: list):
    async with ClientSession() as session:
        responses = await gather(
            get_timestamps(session, steam_ids),
            gather(
                *(
                    get_recently_played_games(session, steam_id)
                    for steam_id in steam_ids
                )
            ),
        )
        info = responses[0]
        for response in responses[1]:
            playtime = get_playtime(response)
            steam_id = playtime["steam_id"]
            if steam_id in info.keys():
                info[steam_id].update(playtime["playtime"])
        return info
