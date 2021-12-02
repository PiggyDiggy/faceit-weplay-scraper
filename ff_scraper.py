from re import compile
from bs4 import BeautifulSoup
from utils import get_page

base_url = "https://faceitfinder.com/ru"
link_pattern = compile(r"/profile/\d+")


def extract_link(soup: BeautifulSoup):
    text = soup.script.text
    link = link_pattern.search(text)
    return link.group()


def get_faceit_info(soup: BeautifulSoup):
    if soup.find(class_="account-faceit-notfound"):
        return "Faceit account not found"
    username = soup.find(class_="account-faceit-title-username").text
    lvl_img = soup.select(".account-faceit-level img")[0]["src"]
    stats = map(lambda s: s.text, soup.select(".account-faceit-stats-single"))
    return {
        "username": username,
        "lvl_img": lvl_img,
        "stats": [*stats]
    }


def get_steam_info(soup: BeautifulSoup):
    account_status = soup.select(".account-steaminfo-row:first-of-type")
    if account_status[0].text == "Аккаунт: Закрытый":
        return "Steam account is private"
    created_at = soup.select(".account-steaminfo-row:nth-of-type(2)")
    total_hours = soup.select(".account-steaminfo-row:nth-of-type(4)")
    hours_in_two_weeks = soup.select(".account-steaminfo-row:nth-of-type(5)")
    info = filter(lambda l: l != [], (created_at,
                                      total_hours, hours_in_two_weeks))
    return list((lst[0].text for lst in info))


async def get_info(session, user: str):
    response = await get_page(session, base_url, method="post", payload={"name": user})
    try:
        link = extract_link(response)
    except AttributeError:
        return f"Player {user} not found"
    page = await get_page(session, f"{base_url}{link}", method="get")
    return {
        "steam_info": get_steam_info(page),
        "faceit_info": get_faceit_info(page)
    }
