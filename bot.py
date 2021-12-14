import discord
from asyncio import gather
from aiohttp import ClientSession
from utils import validate_arguments, get_embed_color, get_thumbnail
from weplay_api import get_ids, get_nicknames_and_avatars
from faceit_api import get_stats_for_multiple_players
from steam_api import get_accounts_info


class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}!")

    async def on_message(self, message):
        content = message.content
        channel = message.channel
        if content.startswith("bb!findplayers"):
            await self.find(content, channel)

    async def find(self, content, channel):
        arguments = content.split()
        if len(arguments) < 3 or len(arguments) > 4:
            raise ValueError(
                "**!findplayers** takes exactly 2 arguments: **lobby id** and **side**"
            )
        lobby_id, side = validate_arguments(content.split())
        message = await channel.send(
            ":manual_wheelchair: **LOADING** :manual_wheelchair:"
        )
        data = await self.get_players_info(lobby_id, side)
        steam_info, faceit_info, media = data["responses"]
        for steam_id in data["ids"]:
            info = {
                "platforms": {"steam_info": {}, "faceit_info": {}},
                "media": media[steam_id],
            }
            if steam_id in steam_info.keys():
                info["platforms"]["steam_info"] = steam_info[steam_id]
            if steam_id in faceit_info.keys():
                info["platforms"]["faceit_info"] = faceit_info[steam_id]
            await self.parse_info_for_embed(info, channel)
        await message.delete()

    async def get_players_info(self, lobby_id, side):
        async with ClientSession() as session:
            ids = await get_ids(session, lobby_id, side)
            responses = await gather(
                get_accounts_info(ids["steam_ids"]),
                get_stats_for_multiple_players(ids["steam_ids"]),
                get_nicknames_and_avatars(session, ids),
            )
            return {"ids": ids["steam_ids"], "responses": responses}

    async def parse_info_for_embed(self, info, channel):
        steam_info, faceit_info = info["platforms"].values()
        if steam_info == {} and faceit_info == {}:
            return await self.send_embed(
                color=0xE74C3C,
                channel=channel,
                user=info["media"],
                description="Аккаунт **steam** скрыт\nАккаунт **faceit** не найден",
            )
        stats = {**steam_info}
        if faceit_info == {}:
            return await self.send_embed(
                color=0xE74C3C,
                channel=channel,
                user=info["media"],
                description="Аккаунт **faceit** не найден",
                stats=stats,
            )
        faceit_nickname = faceit_info.pop("nickname").replace("_", "\_")
        thumbnail = get_thumbnail(faceit_info["ELO"])
        color = get_embed_color(faceit_info["ELO"])
        stats = {**faceit_info, **stats}
        await self.send_embed(
            color=color,
            channel=channel,
            user=info["media"],
            description=f"_Faceit nickname: **{faceit_nickname}**_",
            thumbnail=thumbnail,
            stats=stats,
        )

    async def send_embed(
        self, *, color, channel, user=None, description=None, thumbnail=None, stats={}
    ):
        embed = discord.Embed(description=description, color=color)
        if user:
            embed.set_author(name=user["nickname"], icon_url=user["avatar"])
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        for title, value in stats.items():
            embed.add_field(name=title, value=value.capitalize())
        await channel.send(embed=embed)
