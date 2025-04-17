import discord
import requests
import asyncio
import json
from discord.ext import commands, tasks
from datetime import datetime, timezone

# Load settings
SETTINGS_FILE = "settings.json"
try:
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {"channel_id": None, "notified_users": {}, "addicted_users": {}, "linked_users": {}, "warning_thresholds": {16: "16 hours", 24: "1 day"}, "check_activity": True}

# Torn API Key
TORN_API_KEY = "oYEcdaqBUgUPeAf5"
TORN_API_URL = f"https://api.torn.com/company/?key={TORN_API_KEY}&comment=TornAPI&selections=employees"

# Discord Bot Token
DISCORD_TOKEN = "MTMxNTcwNzMzNzQwMjYxNzkzNg.GrG3kG.-khSgsHco7MQFPPy-s5XTGxL6MoabPfrQgmJH0"
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Ensure message content intent is enabled
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Helper function to save settings
def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_employee_activity.start()
    auto_verify_and_sync.start()

@bot.command(name="set_channel")
@commands.has_permissions(administrator=True)
async def set_channel(ctx, channel: discord.TextChannel):
    """Set the channel for inactivity alerts."""
    settings["channel_id"] = channel.id
    save_settings()
    await ctx.send(f"Alerts will be sent to {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def set_thresholds(ctx, *thresholds: int):
    """Set custom warning thresholds (in hours)."""
    settings["warning_thresholds"] = {t: f"{t} hours" for t in thresholds}
    save_settings()
    await ctx.send(f"Warning thresholds updated: {', '.join(map(str, thresholds))} hours")

@bot.command()
@commands.has_permissions(administrator=True)
async def toggle_checking(ctx):
    """Enable or disable activity checking."""
    settings["check_activity"] = not settings.get("check_activity", True)
    save_settings()
    status = "enabled" if settings["check_activity"] else "disabled"
    await ctx.send(f"Employee activity checking is now {status}.")

@tasks.loop(minutes=5)
async def auto_verify_and_sync():
    """Automatically promotes verified users and syncs ARS roles every 5 minutes."""
    print("[Auto Verify & Sync] Running promote_verified and sync_ars...")

    for guild in bot.guilds:
        verified_role = discord.utils.get(guild.roles, name="verified")
        employee_role = discord.utils.get(guild.roles, name="Employee")
        ars_role = discord.utils.get(guild.roles, name="ARS")

        if not verified_role or not employee_role or not ars_role:
            print("❌ One or more required roles ('verified', 'Employee', 'ARS') not found.")
            continue

        updated_verified = 0
        added_ars = 0
        removed_ars = 0

        # Promote verified users to Employee and remove verified role
        for member in guild.members:
            if verified_role in member.roles:
                if employee_role not in member.roles:
                    try:
                        await member.add_roles(employee_role)
                        updated_verified += 1
                        print(f"✅ Promoted: {member.display_name} → Employee")
                    except Exception as e:
                        print(f"⚠️ Error promoting {member.display_name}: {e}")
                try:
                    await member.remove_roles(verified_role)
                except Exception:
                    pass

        # Fetch Torn company employee list
        data = await fetch_torn_data()
        if not data or "company_employees" not in data:
            print("⚠️ Could not retrieve Torn employee data.")
            continue

        torn_names = [info["name"].lower() for info in data["company_employees"].values()]

        # Add ARS role if name in Torn list, or remove if not
        for member in guild.members:
            has_employee = employee_role in member.roles
            has_ars = ars_role in member.roles
            name_match = any(torn_name in member.display_name.lower() for torn_name in torn_names)

            if has_employee and not has_ars and name_match:
                try:
                    await member.add_roles(ars_role)
                    added_ars += 1
                    print(f"✅ ARS added to: {member.display_name}")
                except Exception as e:
                    print(f"⚠️ Failed to add ARS to {member.display_name}: {e}")

            elif has_ars and not name_match:
                try:
                    await member.remove_roles(ars_role)
                    removed_ars += 1
                    print(f"❌ ARS removed from: {member.display_name} (Not in company)")
                except Exception as e:
                    print(f"⚠️ Failed to remove ARS from {member.display_name}: {e}")

        print(f"[Sync Summary] Verified promoted: {updated_verified}, ARS added: {added_ars}, ARS removed: {removed_ars}")




@bot.command(name='veri')
@commands.has_permissions(manage_roles=True)
async def promote_verified(ctx):
    """Promotes verified users to ARS and removes verified role."""
    guild = ctx.guild
    verified_role = discord.utils.get(guild.roles, name="verified")
    ars_role = discord.utils.get(guild.roles, name="Employee")

    if not verified_role or not ars_role:
        await ctx.send("❌ Either 'verified' or 'ARS' role not found.")
        return

    updated_count = 0

    for member in guild.members:
        if verified_role in member.roles:
            if ars_role not in member.roles:
                try:
                    await member.add_roles(ars_role)
                    await member.remove_roles(verified_role)
                    updated_count += 1
                    print(f"✅ Updated: {member.name}")
                except discord.Forbidden:
                    print(f"❌ Permission denied for {member.name}")
                except discord.HTTPException as e:
                    print(f"⚠️ HTTP error for {member.name}: {e}")

    await ctx.send(f"✅ Promotion complete. {updated_count} users were moved to ARS.")


async def fetch_torn_data():
    """Fetches employee data from Torn API."""
    response = requests.get(TORN_API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching Torn data")
        return None

@bot.command(name="list")
async def list_employees(ctx):
    """List all employee names from the Torn company."""
    data = await fetch_torn_data()
    if not data or "company_employees" not in data:
        await ctx.send("⚠️ Could not retrieve employee data.")
        return

    employee_names = [info["name"] for info in data["company_employees"].values()]
    employee_list = "\n".join(f"• {name}" for name in sorted(employee_names, key=str.lower))

    # Split into chunks if message too long
    chunks = [employee_list[i:i+1900] for i in range(0, len(employee_list), 1900)]
    for chunk in chunks:
        await ctx.send(f"👥 Company Employees:\n{chunk}")

@bot.command(name="sync_ars")
@commands.has_permissions(manage_roles=True)
async def sync_ars(ctx):
    """Adds ARS role to promoted employees whose names match Torn employees."""
    guild = ctx.guild
    ars_role = discord.utils.get(guild.roles, name="ARS")
    employee_role = discord.utils.get(guild.roles, name="Employee")

    if not ars_role or not employee_role:
        await ctx.send("❌ Could not find 'ARS' or 'Employee' role.")
        return

    # Fetch Torn company data
    data = await fetch_torn_data()
    if not data or "company_employees" not in data:
        await ctx.send("⚠️ Could not retrieve Torn employee data.")
        return

    torn_names = [info["name"].lower() for info in data["company_employees"].values()]
    updated_count = 0

    for member in guild.members:
        if employee_role in member.roles and ars_role not in member.roles:
            print(f"Checking {member.display_name}...")
            # Check if name from Discord appears in Torn employee list (case insensitive)
            if any(torn_name.lower() in member.display_name.lower() for torn_name in torn_names):

            #if any(name in member.name.lower() for name in torn_names):
                try:
                    await member.add_roles(ars_role)
                    updated_count += 1
                    print(f"✅ Gave ARS to {member.display_name}")
                except discord.Forbidden:
                    print(f"❌ Permission denied for {member.display_name}")
                except discord.HTTPException as e:
                    print(f"⚠️ HTTP error: {e}")

    await ctx.send(f"✅ ARS synced. {updated_count} members updated.")


@tasks.loop(hours=1)
async def check_employee_activity():
    """Checks for inactive employees and alerts Discord."""
    if not settings.get("check_activity", True):
        print("Activity checking is disabled.")
        return
    
    if settings["channel_id"] is None:
        print("No channel set for alerts.")
        return  # No channel set

    channel = bot.get_channel(settings["channel_id"])
    if not channel:
        print("Invalid channel ID in settings")
        return

    data = await fetch_torn_data()
    if not data or "company_employees" not in data:
        print("No employee data found.")
        return

    current_time = datetime.now(timezone.utc).timestamp()
    time = datetime.fromtimestamp(current_time).strftime("%d %H:%M")
    list2 = time.split(" ")
    #day = list2[0]
    hour = list2[1]
    
    print(list2)
    print(f"Checking employee activity at {time}")

    warning_thresholds = settings.get("warning_thresholds", {16: "16 hours", 24: "1 day"})
    addiction_threshold = settings.get("addiction_threshold", -15)
    
    for torn_id, info in data["company_employees"].items():
        effectiveness = info.get("effectiveness", {})
        addiction = effectiveness.get("addiction", 0)
        print(addiction)
        last_action = info.get("last_action", {})
        last_seen = last_action.get("timestamp", 0)
        relative = last_action.get("relative", "Unknown")

        if last_seen == 0:
            print(f"Skipping {info['name']} - No last seen timestamp.")
            continue  # Skip if no timestamp available

        inactive_hours = (current_time - last_seen) / 3600
        if inactive_hours < 0:
            print(f"Skipping {info['name']} - Negative inactivity time detected.")
            continue  # Skip erroneous data
        
        print(f"{info['name']} inactive for {inactive_hours:.2f} hours.")

        for threshold, label in warning_thresholds.items():
            if inactive_hours >= threshold:
                if settings["notified_users"].get(torn_id) != label:
                    discord_id = settings["linked_users"].get(str(torn_id))  # Ensure Torn ID is a string
                    mention = f"<@{discord_id}>" if discord_id else f"**{info['name']}**"
                    message = f"⚠️ {mention} has been inactive for **{label}**! (Last seen: {relative})"
                    print(f"Sending alert: {message}")
                    await channel.send(message)
                    settings["notified_users"][torn_id] = label  # Mark as notified
                    save_settings()
                break  # Prevent duplicate alerts
        print(f"Addiction {addiction} \nThreshold {addiction_threshold}\n{addiction} <= {addiction_threshold}\n {addiction <= addiction_threshold}")    
        if addiction <= addiction_threshold:
            #print("Addiction level check")
            if settings["addicted_users"].get(torn_id) != 'addicted':
                discord_id = settings["linked_users"].get(str(torn_id))
                mention = f"<@{discord_id}>" if discord_id else f"**{info['name']}**"
                message = f"⚠️ {mention} has an addiction level of **{addiction}**! (Please Rehab! by Sunday)"
                print(f"Sending alert: {message}")
                await channel.send(message)
                settings["addicted_users"][torn_id] = "addicted"
                save_settings()
            break  # Prevent duplicate alerts

@bot.command(name='link')
@commands.has_permissions(administrator=True)
async def link_torn(ctx, torn_id: str, member: discord.Member):
    """Links a Torn ID to a Discord Member."""
    settings.setdefault("linked_users", {})[str(torn_id)] = member.id  # Ensure ID is stored as string
    save_settings()
    await ctx.send(f"Linked Torn ID {torn_id} to {member.mention}")

bot.run(DISCORD_TOKEN)
