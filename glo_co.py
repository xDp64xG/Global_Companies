import discord
from discord.ext import commands
from tasks.news_applications_training import initialize_tasks
from helpers.config_utils import ConfigUtils
from commands import register_commands

TOKEN = "MTMxNTcwNzMzNzQwMjYxNzkzNg.GrG3kG.-khSgsHco7MQFPPy-s5XTGxL6MoabPfrQgmJH0"

# Initialize ConfigUtils
config_utils = ConfigUtils(base_directory="./data/config")

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="=", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    #await initialize_tasks()  # Start all scheduled tasks

# Register bot commands
register_commands(bot)

# Run bot
bot.run(TOKEN)
