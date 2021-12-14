from utils import request
from aiohttp import ClientSession

base_url = "https://api.weplay.tv"
default_avatar = "https://static-prod.weplay.tv/2019-09-13/1e4b1366e9876217059a373ed871f504.png"


def extract_links(data: dict, side: str):
    team = data["team_left"] if side == "left" else data["team_right"]
    return {
        "steam_ids": [member["steam_id"] for member in team],
        "weplay_ids": [str(member["_id"]) for member in team]
    }


async def get_ids(session: ClientSession, lobby_id: str, side: str):
    response = await request(
        session, f"{base_url}/csgo-match-processor/v1/matches/{lobby_id}", "get", verify_ssl=False)
    ids = extract_links(response, side)
    return ids


async def get_nicknames_and_avatars(session: ClientSession, ids: dict):
    ids_str = ",".join(ids["weplay_ids"])
    response = await request(
        session, f"{base_url}/user-management-service/v3/users?filter__user_id__in={ids_str}", "get", verify_ssl=False)
    users = response["data"]
    data = {}
    for steam_id, user in zip(ids["steam_ids"], users):
        if "avatar_path" in user.keys():
            data[steam_id] = {"nickname": user["nickname"],
                              "avatar": user["avatar_path"]}
        else:
            data[steam_id] = {"nickname": user["nickname"],
                              "avatar": default_avatar}
    return data
