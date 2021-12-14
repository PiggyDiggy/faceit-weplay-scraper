from re import compile
from time import gmtime, strftime
from aiohttp import ClientSession
from bs4 import BeautifulSoup

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
}
lobby_id_pattern = compile(r"\d+$")
level_colors = [
    0xEEEEEE,
    0x1CE400,
    0x1CE400,
    0xFFC800,
    0xFFC800,
    0xFFC800,
    0xFFC800,
    0xFF6309,
    0xFF6309,
    0xFE1F00,
]
level_mapping = {
    2001: 10,
    1851: 9,
    1701: 8,
    1551: 7,
    1401: 6,
    1251: 5,
    1101: 4,
    951: 3,
    801: 2,
    1: 1,
}
base_lvl_icon_url = "https://faceitfinder.com/resources/ranks/skill_level_{}_lg.png"


async def request(
    session: ClientSession, url: str, method: str, headers: dict = headers, **kwargs
):
    try:
        async with session.request(method, url, headers=headers, **kwargs) as response:
            if response.content_type == "application/json":
                return await response.json()
            return await response.text()
    except Exception as exc:
        print(f"Unable to request url {url} due to {exc}")


async def get_page(
    session: ClientSession, url: str, method: str, headers: dict = headers, **kwargs
):
    response = await request(session, url, method, headers, **kwargs)
    soup = BeautifulSoup(response, "lxml")
    return soup


def validate_arguments(args: list):
    lobby_id, side = lobby_id_pattern.search(args[1]), args[2]
    if not lobby_id:
        raise ValueError(
            "**Lobby id** argument must be either **link to a lobby** or **lobby id** itself"
        )
    if side not in ("left", "right", "both"):
        raise ValueError("**Side** argument can only take **left** or **right** value")
    return lobby_id.group(), side


def get_level(elo: int):
    for min_elo, lvl in level_mapping.items():
        if elo >= min_elo:
            return lvl


def get_embed_color(elo: str):
    lvl = get_level(int(elo))
    return level_colors[lvl - 1]


def get_thumbnail(elo: str):
    lvl = get_level(int(elo))
    return base_lvl_icon_url.format(lvl)


def get_date(secs: int):
    struct_time = gmtime(secs)
    return strftime(r"%d.%m.%Y", struct_time)