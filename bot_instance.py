import discord
from discord.ext import commands

intents = discord.Intents.default()
#intents = discord.Intents.default()
intents.messages = True


# Update intents to include message_content

intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="=", intents=intents)
