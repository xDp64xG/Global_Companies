import asyncio
import discord
from discord.ext import tasks
from datetime import datetime
#from .utils import load_json, save_json, fetch_data, resolve_target, send_or_edit_message
from helpers.company_utils import CompanyUtils
from .utils import *


CONFIG_FILE = "./data/config/config.json"
LAST_ACTION_FILE = "./data/company_checker/Employee/employee_data.json"
LOYALTY_TRACKING_FILE = "loyalty_tracking.json"
Company_Positions_File = "./data/company_information/company_data.json"

def get_business_position(json_data, business_index, position_name):
    """Retrieve the business position requirements safely."""
    
    business_key = str(business_index)
    business_data = json_data.get(business_key, {})

    if not business_data:
        print(f"[WARNING] Business index {business_index} not found in JSON.")
        return {"Position": "Unknown", "Requirements": {}}

    positions = business_data.get("Positions", {})
    position_data = positions.get(position_name, {})

    if not position_data:
        print(f"[WARNING] Position '{position_name}' not found in business type '{business_data.get('Type', 'Unknown')}'.")
        return {"Position": "Unknown", "Requirements": {}}

    return {
        "Position": position_name,
        "Requirements": position_data
    }

async def generate_employee_embed(api_key, company_type, employee_url, news_channel, bonus_channel):
    """Generate an embed with employee statistics."""
    employee_data = fetch_data(employee_url).get("company_employees", {})
    last_actions = await load_json_async(LAST_ACTION_FILE)

    

    stat_emojis = {
        "Manual Labor": "🔨",
        "Intelligence": "🧠",
        "Endurance": "💪",
    }
    
    if "employees" not in last_actions:
        last_actions["employees"] = {}
    
    embeds = []
    for emp_id, details in employee_data.items():
        name = details.get("name", "Unknown")
        position = details.get("position", "N/A")
        loyalty = details.get("days_in_company", 0)
        wage = details.get("wage", "N/A")
        manual = details.get("manual_labor", 0)
        intelligence = details.get("intelligence", 0)
        endurance = details.get("endurance", 0)
        
        last_action = details.get("last_action", {}).get("relative", "N/A")
        effectiveness = details.get("effectiveness", {})
        name_link = f"[{name}](https://www.torn.com/profiles.php?XID={emp_id})"

        # Position update notification
        previous_position = last_actions["employees"].get(name, {}).get("Position", "N/A")
        if previous_position != position and previous_position != "N/A":
            if news_channel:
                embed = discord.Embed(
                    title="Position Update",
                    description=f"📢 **{name}** switched from **{previous_position}** to **{position}**.",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                await news_channel.send(embed=embed)

        # Loyalty milestone notification
        if loyalty % 30 == 0 and loyalty > 0:
            if await update_loyalty_tracking(api_key, emp_id, loyalty):
                if bonus_channel:
                    await bonus_channel.send(
                        f"🎉 {name_link} has reached {loyalty} days of loyalty! Consider issuing a bonus! 🎉"
                    )

        # Stats comparison
        #positions = json.load(open(Company_Positions_File, "r"))
        positions = await load_json_async(Company_Positions_File)
        result = get_business_position(positions, company_type, position)
        _, requirements = process_result(result)
        stat_comparison = []

        # Known stats
        known_stats = {
            "Manual Labor": manual,
            "Intelligence": intelligence,
            "Endurance": endurance,
        }

        # Compare stats with requirements
        for stat, required_value in requirements.items():
            current_value = known_stats.get(stat, 0)
            diff = current_value - required_value
            emoji = stat_emojis.get(stat, "")
            stat_comparison.append(f"{emoji} {stat}: {current_value:,} ({'+' if diff >= 0 else ''}{diff:,})")

        # Find the missing stat not in requirements
        missing_stat = next(
            (stat for stat in known_stats if stat not in requirements), None
        )
        if missing_stat:
            missing_stat_value = known_stats[missing_stat]
            emoji = stat_emojis.get(missing_stat, "")
            stat_comparison.append(f"{emoji} {missing_stat}: {missing_stat_value:,} (Not required)")

        # Add total stats to the end of the Stats field
        total_stat_value = sum(known_stats.values())
        stat_comparison.append(f"**Total Stats:** {total_stat_value:,}")

        # Update last actions
        last_actions["employees"][name] = {
            "Employee ID": emp_id,
            "last action": last_action,
            "Position": position,
            "Loyalty": loyalty,
            "Wage": wage,
            "Effectiveness": effectiveness,
            "Working Stats": known_stats,
        }

        # Build the embed
        embed = discord.Embed(
            title=name,
            url=f"https://www.torn.com/profiles.php?XID={emp_id}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="General Info",
            value=(f"**Position:** {position}\n"
                   f"**Loyalty:** {loyalty} days\n"
                   f"**Wage:** ${wage:,}\n"
                   f"**Last Online:** {last_action}"),
            inline=False
        )
        embed.add_field(
            name="Stats",
            value="\n".join(stat_comparison),  # Include missing stat and total stats
            inline=True
        )
        embed.add_field(
            name="Effectiveness",
            value=(f"**Settled in:** {effectiveness.get('settled_in', 'N/A')}\n"
                   f"**Merits:** {effectiveness.get('merits', 'N/A')}\n"
                   f"**Director Education:** {effectiveness.get('director_education', 'N/A')}\n"
                   f"**Management:** {effectiveness.get('management', 'N/A')}\n"
                   f"**Addiction:** {effectiveness.get('addiction', 'N/A')}\n"
                   f"**Inactivity:** {effectiveness.get('inactivity', 'N/A')}\n"
                   f"**Total Effectiveness:** {effectiveness.get('total', 'N/A')}")
        )
        embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        embeds.append(embed)

    # Save last actions to JSON
    await save_json_async(last_actions, LAST_ACTION_FILE)
    return embeds

def generate_training_report(api_key):
    """Generate and return a detailed training report with train needs."""
    
    company_utils = CompanyUtils(api_key)
    employee_data = company_utils.fetch_employee_data()
    training_report = []
    
    for employee, stats in employee_data.items():
        missing_stats = stats.get("missing_stats", {})
        train_needed = stats.get("trains_needed", {})

        report_line = f"**{employee}** - Missing: {', '.join(missing_stats.keys()) if missing_stats else 'None'}"

        if train_needed:
            report_line += f", Trains Needed: {', '.join([f'{k}: {v}' for k, v in train_needed.items()])}"

        training_report.append(report_line)

    return "\n".join(training_report)


async def update_loyalty_tracking(api_key, emp_id, milestone):
    loyalty_data = await CompanyUtils.get_company_data(api_key, LOYALTY_TRACKING_FILE)
    loyalty_data.setdefault(emp_id, [])
    if milestone not in loyalty_data[emp_id]:
        loyalty_data[emp_id].append(milestone)
        await CompanyUtils.save_company_data(api_key, LOYALTY_TRACKING_FILE, loyalty_data)
        return True
    return False

def process_result(result):
    """Process result to extract position and requirements."""
    
    if not isinstance(result, dict):
        print(f"[ERROR] Expected a dictionary but got {type(result).__name__}. Value: {result}")
        return "Unknown Position", {}  # Return safe defaults

    position = result.get("Position", "Unknown Position")
    requirements = result.get("Requirements", {})

    if position == "Unassigned" or not requirements:
        print(f"[INFO] Skipping unassigned or missing position: {position}")
        return position, {}

    return position, requirements

@tasks.loop(hours=1)
async def update_employee_stats(bot, config, api_key, employee_url, profile_url):
    """Update employee statistics hourly."""
    try:
        channel_id = config.get("channel_id")
        print(f"[DEBUG] API Key: {api_key}\nChannel ID: {channel_id}")
        if not isinstance(channel_id, int):
            return
        company_type = fetch_data(profile_url).get("company", {}).get("company_type", {})
        
        news_channel_id = await get_channel_id(api_key, "news")
        news_channel = bot.get_channel(news_channel_id)
        bonus_channel_id = await get_channel_id(api_key, "bonuses")
        bonus_channel = bot.get_channel(bonus_channel_id)
        
        embeds = await generate_employee_embed(api_key, company_type, employee_url, news_channel, bonus_channel)
        await send_or_edit_message(bot, api_key, "employees", channel_id, embeds)
    except Exception as e:
        print(f"[ERROR] Exception in update_employee_stats for API key '{api_key}': {e}")

async def get_channel_id(api_key, section):
    config = await load_json_async(CONFIG_FILE)
    return config.get("api_keys", {}).get(api_key, {}).get(section, {}).get("channel_id")
