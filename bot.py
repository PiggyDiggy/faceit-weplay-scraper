import discord
import asyncio
import aiohttp
from ff_scraper import get_info
from utils import validate_arguments, get_embed_color
from weplay_scraper import get_ids, get_nicknames_and_avatars


class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}!")

    async def on_message(self, message):
        content = message.content
        channel = message.channel
        if content.startswith("bb!findplayers"):
            try:
                await self.find(content, channel)
            except ValueError as err:
                embed = discord.Embed(description=str(err), color=0xe74c3c)
                return await channel.send(embed=embed)
        elif content.startswith("bb!test"):
            await self.parse_info_for_embed({
                "platforms":
                    {'steam_info': ['Аккаунт создан: 02.06.2012', 'Всего часов в CS:GO: скрыто', 'Часов CS:GO за 2 недели: скрыто'],
                     'faceit_info': {'username': 'GennadiyPig', 'lvl_img': '/resources/ranks/skill_level_6_lg.png', 'stats': ['Матчей: 17', 'ELO: 1416', 'K/D: 1.18', 'Побед: 71.0%', 'Побед: 12', 'HS: 49.8%']}},
                "media":
                    {'nickname': 'BOT Bull', 'avatar': 'https://static-prod.weplay.tv/users/avatar/user_295459_aa67d41c9fb71984864232202eb056b2.8C8F5C-2D360E-4F371F.png'}
            },
                channel
            )

    async def find(self, content, channel):
        arguments = content.split()
        if len(arguments) < 3 or len(arguments) > 4:
            raise ValueError(
                "**!findplayers** takes exactly 2 arguments: **lobby id** and **side**")
        lobby_id, side = validate_arguments(content.split())
        info_dict = await self.get_all_players_info(lobby_id, side)
        players_info, media = info_dict.values()
        for i, player in enumerate(players_info):
            info = {"platforms": player, "media": media[i]}
            await self.parse_info_for_embed(info, channel)

    async def get_all_players_info(self, lobby_id, side):
        async with aiohttp.ClientSession() as session:
            ids = await get_ids(session, lobby_id, side)
            res = await asyncio.gather(*(get_info(session, user_id["steam_id"]) for user_id in ids))
            media = await get_nicknames_and_avatars(session, ids)
            return {"res": res, "media": media}

    async def parse_info_for_embed(self, info, channel):
        if not isinstance(info["platforms"], dict):
            return await self.send_embed(color=0xe74c3c, channel=channel, user=info["media"], description=info["platforms"])
        steam_info, faceit_info = info["platforms"].values()
        stats = []
        if isinstance(steam_info, list):
            stats.extend(s.split(": ") for s in steam_info)
        if isinstance(faceit_info, dict):
            faceit_nickname = faceit_info["username"].replace("_", "\_")
            color = get_embed_color(faceit_info["lvl_img"])
            stats.extend(s.split(": ") for s in faceit_info["stats"])
            return await self.send_embed(
                color=color,
                channel=channel,
                user=info["media"],
                description=f"_Faceit nickname: **{faceit_nickname}**_",
                thumbnail=f"https://faceitfinder.com{faceit_info['lvl_img']}",
                stats=stats)
        await self.send_embed(color=0xe74c3c, channel=channel, user=info["media"], description=faceit_info)

    async def send_embed(self, *, color, channel, user=None, description=None, thumbnail=None, stats=[]):
        embed = discord.Embed(
            description=description,
            color=color
        )
        if user:
            embed.set_author(name=user["nickname"], icon_url=user["avatar"])
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        for title, value in stats:
            embed.add_field(name=title, value=value.capitalize())
        await channel.send(embed=embed)
