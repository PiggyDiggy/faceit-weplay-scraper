from utils import request

base_url = "https://api.weplay.tv"
default_avatar = "https://static-prod.weplay.tv/2019-09-13/1e4b1366e9876217059a373ed871f504.png"


def extract_links(data: dict, side: str):
    team = data["team_left"] if side == "left" else data["team_right"]
    return [
        {"steam_id": member["steam_id"], "weplay_id": str(member["_id"])} for member in team]


async def get_ids(session, lobby_id: str, side: str):
    response = await request(
        session, f"{base_url}/csgo-match-processor/v1/matches/{lobby_id}", "get")
    ids = extract_links(response, side)
    return ids


async def get_nicknames_and_avatars(session, user_ids: list):
    ids_str = ",".join(lst["weplay_id"] for lst in user_ids)
    response = await request(
        session, f"{base_url}/user-management-service/v3/users?filter__user_id__in={ids_str}", "get")
    users = response["data"]
    data = []
    for user in users:
        if "avatar_path" in user.keys():
            data.append(
                {"nickname": user["nickname"], "avatar": user["avatar_path"]})
        else:
            data.append(
                {"nickname": user["nickname"], "avatar": default_avatar})
    return data
