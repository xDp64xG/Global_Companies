from helpers.company_utils import CompanyUtils
from helpers.api_utils import ApiUtils
import asyncio
import discord
from discord.ext import tasks
from datetime import datetime
import os
from .utils import *

CONFIG_FILE = "./data/config/config.json"
PROFIT_LOG_FILE = "./data/company_checker/Profits/profit_log.json"
PROFIT_TRACKING_FILE = "./data/company_checker/Profits/profit_tracking.json"
STOCK_LOG_FILE = "./data/company_checker/Stocks/daily_stock_log.json"

async def ensure_json_file(file_path, default_data={}):
    if not os.path.exists(file_path):
        await save_json_async(default_data, file_path)

async def generate_company_embed(api_key, urls):
    await ensure_json_file(PROFIT_LOG_FILE, {api_key: {"entries": []}})
    await ensure_json_file(STOCK_LOG_FILE, {api_key: {"entries": []}})

    profile_url = urls.get("profile", "")
    stock_url = urls.get("stock", "")
    detailed_url = urls.get("detailed", "")

    if not profile_url or not stock_url or not detailed_url:
        print(f"[ERROR] Missing URLs for API key {api_key}: {urls}")
        return []

    profile_data = fetch_data(profile_url) or {}
    stock_data = fetch_data(stock_url) or {}
    company_data = fetch_data(detailed_url) or {}

    if not profile_data or not company_data:
        print(f"[ERROR] Missing company data for API key {api_key}")
        return []

    company_name = profile_data.get("company", {}).get("name", "Unknown")
    company_funds = company_data.get("company_detailed", {}).get("company_funds", 0)
    popularity = company_data.get("company_detailed", {}).get("popularity", 0)
    efficiency = company_data.get("company_detailed", {}).get("efficiency", 0)
    environment = company_data.get("company_detailed", {}).get("environment", 0)
    trains_available = company_data.get("company_detailed", {}).get("trains_available", 0)
    advertising_budget = company_data.get("company_detailed", {}).get("advertising_budget", 0)
    current_profit = profile_data['company'].get('daily_income', 0)
    current_customers = profile_data['company'].get('daily_customers', 0)
    rating = profile_data['company'].get('rating', 0)

    company_utils = CompanyUtils(api_key)
    profit_stats = await company_utils.update_profit_tracking(current_profit, current_customers, is_daily_update=True)

    if not profit_stats:
        profit_stats = {"total_profit": 0, "average_profit": 0, "highest_profit": 0, "lowest_profit": 0}

    embeds = []

    # Main company profile embed
    base_embed = discord.Embed(
        title=f"Company Profile: {company_name}",
        color=discord.Color.blue()
    )
    base_embed.add_field(name="Company Funds", value=f"${company_funds:,}", inline=True)
    base_embed.add_field(name="Popularity", value=f"{popularity}", inline=True)
    base_embed.add_field(name="Efficiency", value=f"{efficiency}", inline=True)
    base_embed.add_field(name="Environment", value=f"{environment}", inline=True)
    base_embed.add_field(name="Rating", value=f"{rating}", inline=True)
    base_embed.add_field(name="Current Profit", value=f"${current_profit:,}", inline=True)
    base_embed.add_field(name="Current Customers", value=f"{current_customers}", inline=True)
    base_embed.add_field(name="Trains Available", value=f"{trains_available}", inline=True)
    base_embed.add_field(name="Advertising Budget", value=f"${advertising_budget:,}", inline=True)
    base_embed.add_field(name="Total Profit", value=f"${profit_stats['total_profit']:,}", inline=False)
    base_embed.add_field(name="Average Daily Profit", value=f"${profit_stats['average_profit']:,}", inline=True)
    base_embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    embeds.append(base_embed)

    # Stock item embeds
    current_embed = discord.Embed(
        title="Stock Report",
        color=discord.Color.blue()
    )
    field_count = 0

    for item, details in stock_data.get('company_stock', {}).items():
        stock = details.get('in_stock', 0)

        if stock < 1000:
            warning = "⚠️ Critical stock level! <@&1321602638357336187> get ahold of the <@&1313749451998761010>"
        elif stock < 1500:
            warning = "Stock is looking good!"
        elif stock < 1750:
            warning = f"⚠️ Low stock detected! Only {stock} left. <@&1321602638357336187> get ahold of the <@&1313749451998761010>"
        else:
            warning = "🎉 High stock! Switch up the staff for more Salespersons <@&1321602638357336187>"

        """stock_value = (
            f"Cost: ${details.get('cost', 0):,}\n"
            f"In Stock: {details.get('in_stock', 0)}\n"
            f"Sold Amount: {details.get('sold_amount', 0)}\n"
            f"Price: ${details.get('price', 0):,}\n"
            f"RRP: ${details.get('rrp', 0):,}\n"
            f"Profit: ${details.get('sold_worth', 0):,}\n"
            f"Incoming stock: {details.get('on_order', 0)}"
        )"""
        stock_value = (
            f"**Cost:** ${details.get('cost', 0):,} | **In Stock:** {details.get('in_stock', 0)}\n"
            f"**Sold:** {details.get('sold_amount', 0)} | **Price:** ${details.get('price', 0):,} | **RRP:** ${details.get('rrp', 0):,}\n"
            f"**Profit:** ${details.get('sold_worth', 0):,} | **Incoming:** {details.get('on_order', 0)}\n"
            f"**Alert:** {warning}"
        )

        if field_count + 2 > 25:
            current_embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            embeds.append(current_embed)
            current_embed = discord.Embed(title="Stock Report (continued)", color=discord.Color.blue())
            field_count = 0

        current_embed.add_field(name=f"Stock: {item}", value=stock_value, inline=False)
        current_embed.add_field(name="Stock alert:", value=warning, inline=False)
        field_count += 2

    if field_count > 0:
        current_embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        embeds.append(current_embed)

    return embeds

@tasks.loop(hours=1)
async def post_company_update(bot, company_config, api_key, urls):
    """Post company statistics hourly for a single API key."""

    print(f"[INFO] Processing company update for API Key: {api_key}")

    company_channel_id = company_config.get("channel_id")
    if not isinstance(company_channel_id, int):
        print(f"[ERROR] Invalid company channel ID: {company_channel_id} for API Key: {api_key}")
        return  # Skip to next API key

    # Fetch company and stock data
    company_utils = CompanyUtils(api_key)
    #company_data = company_utils.fetch_company_data()
    company_data = fetch_data(urls.get("profile", "")) or {}
    stock_data = await company_utils.fetch_stock_data()
    print(f'[DEBUG] Company data: {company_data}')
    print(f'[DEBUG] Stock data: {stock_data}')

    # Log profit and stock tracking
    current_profit = company_data.get("company_detailed", {}).get("daily_income", 0)
    current_customers = company_data.get("company_detailed", {}).get("daily_customers", 0)

    await company_utils.update_profit_tracking(current_profit, current_customers, is_daily_update=True)
    await company_utils.log_daily_stock(stock_data)

    # Build and send company embed
    #embed = await generate_company_embed(api_key, urls)
    embeds = await generate_company_embed(api_key, urls)
    for embed in embeds:
        await send_or_edit_message(bot, api_key, "company", company_channel_id, [embed])


    #embed = company_utils.build_company_embed(company_data)

    #channel = bot.get_channel(company_channel_id)
    #if not channel:
        #print(f"[ERROR] Unable to fetch Discord channel: {company_channel_id} for API Key: {api_key}")
        #return  # Skip to next API key

    #message = await channel.send(embed=embed)
    #set_json_key(CONFIG_FILE, f"api_keys.{api_key}.company.message_ids", [message.id])
    
    #await send_or_edit_message(bot, api_key, "company", company_channel_id, [embed])

    # Post company graphs
    #await post_company_graphs(bot, api_key, company_channel_id)

GRAPH_MESSAGE_LOG = "./data/company_checker/graph_messages.json"

async def post_company_graphs(bot, api_key, company_channel_id):
    """Generate and post company graphs in Discord."""
    
    company_utils = CompanyUtils(api_key)
    stock_graph, profit_graph = company_utils.generate_graphs()

    # Ensure paths are valid
    if stock_graph is None or profit_graph is None:
        print(f"[ERROR] Graph generation failed. Skipping post for {api_key}.")
        return

    if not os.path.exists(stock_graph) or not os.path.exists(profit_graph):
        print(f"[ERROR] Graph files not found. Skipping post for {api_key}.")
        return

    channel = bot.get_channel(company_channel_id)
    if not channel:
        print(f"[ERROR] Unable to fetch Discord channel: {company_channel_id}")
        return

    # Load the previous message IDs for graphs
    message_log = await load_json_async(GRAPH_MESSAGE_LOG)
    previous_messages = message_log.get(api_key, [])

    # Delete old graph messages
    for msg_id in previous_messages:
        try:
            message = await channel.fetch_message(msg_id)
            await message.delete()
        except Exception as e:
            print(f"[WARNING] Failed to delete old graph message {msg_id}: {e}")

    # Create new embed for company graphs
    embed = discord.Embed(
        title=f"📊 Company Performance Metrics - {api_key}",
        description="Latest stock and profit trends.",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )

    # Attach graph images
    files = []
    if os.path.exists(stock_graph):
        files.append(discord.File(stock_graph, filename="stock_graph.png"))
    if os.path.exists(profit_graph):
        files.append(discord.File(profit_graph, filename="profit_graph.png"))

    # Send the new message with graphs
    message = await channel.send(embed=embed, files=files)

    # Store the new message ID for future deletion
    set_json_key(GRAPH_MESSAGE_LOG, api_key, [message.id])
    print(f"[INFO] Company graphs posted. Message ID: {message.id}")

def generate_api_urls(api_key):
        base_url = f"https://api.torn.com/company/?key={api_key}&comment=Project_Glo_Co_Bot"
        return {
            "profile": f"{base_url}{api_key}&selections=profile",
            "stock": f"{base_url}{api_key}&selections=stock",
            "employees": f"{base_url}{api_key}&selections=employees",
            "detailed": f"{base_url}{api_key}&selections=detailed",
            "applications": f"{base_url}{api_key}&selections=applications",
            "news": f"{base_url}{api_key}&selections=news",
        }

@tasks.loop(hours=2)
async def monitor_company_funds(bot, api_key, news_config, company_funds_url):
    """Monitor company funds and post warnings if low."""
    try:
        print(f"Company Funds url: {company_funds_url}  ")
        company_funds_data = fetch_data(company_funds_url)
        company_funds = company_funds_data.get("company_detailed", {}).get("company_funds", 0)
        fund_threshold = news_config.get("company_vault", 0)
        
        if fund_threshold and company_funds < fund_threshold:
            channel_id = news_config.get("channel_id")
            target = await resolve_target(channel_id)
            
            if target:
                embed = discord.Embed(
                    title="⚠️ Low Company Funds",
                    description=f"The company funds have dropped below ${fund_threshold:,}. Action required!",
                    color=discord.Color.red()
                )
                await target.send(embed=embed)
    except Exception as e:
        print(f"[ERROR] Exception in monitor_company_funds: {e}")
