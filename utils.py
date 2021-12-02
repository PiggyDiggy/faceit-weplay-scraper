from re import compile
from typing import Union
from bs4 import BeautifulSoup

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
}
lobby_id_pattern = compile(r"\d+$")
level_colors = [0xeeeeee, 0x1ce400, 0x1ce400, 0xffc800,
                0xffc800, 0xffc800, 0xffc800, 0xff6309, 0xff6309, 0xfe1f00]


async def request(session, url: str, method: str, payload: Union[dict, None] = None):
    try:
        async with session.request(method, url, data=payload, headers=headers, verify_ssl=False) as response:
            if response.content_type == "application/json":
                return await response.json()
            return await response.text()
    except Exception as exc:
        print(f"Unable to request url {url} due to {exc}")


async def get_page(session, url: str, method: str, payload: Union[dict, None] = None):
    response = await request(session, url, method, payload)
    soup = BeautifulSoup(response, "lxml")
    return soup


def validate_arguments(args):
    lobby_id, side = lobby_id_pattern.search(args[1]), args[2]
    if not lobby_id:
        raise ValueError(
            "**Lobby id** argument must be either **link to a lobby** or **lobby id** itself")
    if side not in ("left", "right", "both"):
        raise ValueError(
            "**Side** argument can only take **left** or **right** value")
    return lobby_id.group(), side


def get_embed_color(string):
    for char in string[::-1]:
        if char.isdigit():
            return level_colors[int(char) - 1]
