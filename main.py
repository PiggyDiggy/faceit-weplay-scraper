from bot import MyClient
from tokens import discord_bot_token


def main():
    client = MyClient()
    client.run(discord_bot_token)


if __name__ == "__main__":
    main()
