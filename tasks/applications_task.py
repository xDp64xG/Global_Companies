import asyncio
import discord
from discord.ext import tasks
from datetime import datetime
#from .utils import load_json, save_json, fetch_data, resolve_target, send_or_edit_message
from .utils import *



APPLICATIONS_SEEN_FILE = "./data/company_checker/Applications/applications_seen.json"

async def generate_application_embeds(api_key, applications_url):
    """Generate embeds for pending applications."""
    data = fetch_data(applications_url).get("applications", {})
    if data:
        seen_applications = load_json_async(APPLICATIONS_SEEN_FILE).get(api_key, {})
        embeds = []
        
        for app_id, details in data.items():
            if app_id in seen_applications:
                continue
            
            user_id = details.get("userID", "N/A")
            name = details.get("name", "Unknown")
            level = details.get("level", "N/A")
            stats = details.get("stats", {})
            status = details.get("status", "N/A")
            expires = datetime.fromtimestamp(details.get("expires", 0)).strftime("%Y-%m-%d %H:%M:%S")
            message = details.get("message", "No message provided.")
            profile_link = f"https://www.torn.com/profiles.php?XID={user_id}"
            
            embed = discord.Embed(
                title="New Application",
                description=f"[{name}]({profile_link})",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Level", value=level, inline=True)
            embed.add_field(name="Manual Labor", value=stats.get("manual_labor", "N/A"), inline=True)
            embed.add_field(name="Intelligence", value=stats.get("intelligence", "N/A"), inline=True)
            embed.add_field(name="Endurance", value=stats.get("endurance", "N/A"), inline=True)
            embed.add_field(name="User Message", value=message, inline=False)
            embed.add_field(name="Status", value=status.capitalize(), inline=True)
            embed.add_field(name="Expires", value=expires, inline=True)
            embed.set_footer(text=f"Application ID: {app_id}")
            
            embeds.append(embed)
            seen_applications[app_id] = details
        
        await save_json_async({api_key: seen_applications}, APPLICATIONS_SEEN_FILE)
        return embeds
    else:
        return None

@tasks.loop(minutes=5)
async def check_applications(bot, config, api_key, applications_url):
    """Check and process applications every 5 minutes."""
    try:
        channel_id = config.get("channel_id")
        print(f"[DEBUG] API Key: {api_key}\nChannel ID: {channel_id}")
        if not isinstance(channel_id, int):
            return
        
        embeds = await generate_application_embeds(api_key, applications_url)
        print("Generated embeds for applications")
        if embeds and embeds != None:
            await send_or_edit_message(bot, api_key, "applications", channel_id, embeds)
    except Exception as e:
        print(f"[ERROR] Exception in check_applications for API key '{api_key}': {e}")