import asyncio
import discord
from discord.ext import tasks
from datetime import datetime
import re
from bs4 import BeautifulSoup
from helpers.company_utils import CompanyUtils
from .utils import *

#from .utils import load_json, save_json, fetch_data, resolve_target, send_or_edit_message

NEWS_LOG_FILE = "./data/company_checker/News/news_log.json"
#TRAINING_COUNTS_FILE = "./data/company_checker/News/training_counts.json"
TRAINING_COUNTS_FILE = "./data/company_checker/Training/training_counts.json"


async def process_company_news(bot, api_key, news_config, urls):
    """Check for new relevant news items and post them using the `send_or_edit_message` function."""
    news_url = urls.get("news", "")
    if not news_url:
        print(f"[ERROR] Missing news URL for API key {api_key}.")
        return
    
    news_data = fetch_data(news_url).get("news", {})
    seen_news = await load_json_async(NEWS_LOG_FILE)
    api_key_str = str(api_key)  # Ensure api_key is a string
    seen_news = seen_news.get(api_key_str, {})
    training_counts = await load_json_async(TRAINING_COUNTS_FILE)
    print(news_config)
    news_channel_id = news_config.get("channel_id")
    training_channel_id = news_config.get("training_channel_id")

    embed = None

    if not isinstance(news_channel_id, int):
        print(f"Invalid channel_id for company: {news_channel_id}")
        return

    target = await resolve_target(bot, news_channel_id)
    if not target:
        print(f"[ERROR] Failed to resolve target for news. Channel ID: {news_channel_id}")
        return

    print("[INFO] Processing company news...")
    embeds_to_send = []

    for news_id, details in news_data.items():
        if news_id in seen_news:
            continue

        raw_news_text = details["news"]
        news_text = re.sub(r'<.*?>', '', raw_news_text)  # Clean HTML tags
        timestamp = datetime.fromtimestamp(details["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        
        #sTART HERE
        # Match day report using a regex
        day_report_match = re.search(r"(\w+) report: .*", news_text)
        if day_report_match:
            day = day_report_match.group(1)  # Extract the day (e.g., "Friday")
            embed = discord.Embed(
                title=f"{day} Report",
                description=news_text,
                color=discord.Color.gold(),
            )

        # Check for accepted applications
        application_match = re.search(
            r'<a href = http://www\.torn\.com/profiles\.php\?XID=\d+>(.*?)</a> has accepted <a href = http://www\.torn\.com/profiles\.php\?XID=\d+>(.*?)</a>\'s application to join the company',
            raw_news_text
        )
        if application_match:
            acceptor = application_match.group(1)
            applicant = application_match.group(2)
            embed = discord.Embed(
                title="Application Accepted",
                description=f"🎉 **{acceptor}** has accepted **{applicant}**'s application to join the company!",
                color=discord.Color.green()
            )

        # Check for company rating changes
        rating_match = re.search(r"the company has (increased|decreased) to rating (\d+)", news_text)
        if rating_match:
            action = rating_match.group(1)
            rating = int(rating_match.group(2))
            description = (
                f"🎉 Congratulations! The company rating has increased to {rating}!"
                if action == "increased"
                else f"😢 The company rating has decreased to {rating}. Let's improve!"
            )
            embed = discord.Embed(
                title="Company Rating Update",
                description=description,
                color=discord.Color.green() if action == "increased" else discord.Color.red(),
            )

        # Check for funds withdrawn or deposited
        if re.search(r"withdrawn\s+\$\S+\s+from the company funds", news_text):
            emoji = get_news_emoji("withdrawn from the company funds")
            embed = discord.Embed(
                title="Company Funds Update",
                description=f"{emoji} {news_text}",
                color=discord.Color.purple(),
            )
        if re.search(r"has made a deposit of \$\S+\s+to the company funds", news_text):
            emoji = get_news_emoji("has made a deposit into the company funds")
            embed = discord.Embed(
                title="Company Funds Update",
                description=f"{emoji} {news_text}",
                color=discord.Color.purple(),
            )

        # Handle training-related news
        if "has been trained by the director" in news_text:
            employee_name = extract_employee_name(raw_news_text)
            if employee_name:
                training_counts[employee_name] = training_counts.get(employee_name, 0) + 1
                await CompanyUtils.save_company_data(api_key, "training_counts.json", training_counts)

        # Handle employee leaving or being fired
        if "has left the company" in news_text or "has been fired from the company" in news_text:
            emoji = get_news_emoji(news_text)
            embed = discord.Embed(
                title="Employee Departure",
                description=f"{emoji} {news_text}",
                color=discord.Color.red(),
            )

        # Add the embed to the list if created
        if embed:
            embed.set_footer(text=f"Posted: {timestamp}")
            embeds_to_send.append(embed)
        
        if not any(e.description == news_text for e in embeds_to_send):
            fallback = discord.Embed(
                title="Company News Update",
                description=news_text,
                color=discord.Color.gold()
            )
            fallback.set_footer(text=f"Posted: {timestamp}")
            embeds_to_send.append(fallback)


        seen_news[news_id] = details

    await save_json_async({api_key_str: seen_news}, NEWS_LOG_FILE)

    # Post grouped training report if training occurred
    if training_counts and training_channel_id:
        training_summary = "\n".join([f"{name}: {count} times" for name, count in training_counts.items()])
        training_embed = discord.Embed(
            title="Training Summary",
            description=f"📘 **Training by Director**:\n{training_summary}",
            color=discord.Color.blue(),
        )
        await send_or_edit_message(bot, api_key, "training", training_channel_id, [training_embed])
        await CompanyUtils.save_company_data(api_key, "training_counts.json", {})


    if embeds_to_send:
        print(f"[INFO] Sending {len(embeds_to_send)} news embeds.")
        await send_or_edit_message(bot, api_key, "news", news_channel_id, embeds_to_send)
    else:
        print("[INFO] No new news to process.")

def get_news_emoji(news_text):
    """Return appropriate emoji based on the news content."""
    if "has been trained by the director" in news_text:
        return "📘"
    if "has left the company" in news_text or "has been fired from the company" in news_text:
        return "🚪"
    if "withdrawn from the company funds" in news_text or "made a deposit" in news_text:
        return "💰"
    return "📰"  # Default emoji

def extract_employee_name(raw_html):
    """Extract employee name from the raw HTML string."""
    soup = BeautifulSoup(raw_html, 'html.parser')
    link = soup.find('a')  # Finds the first <a> tag
    return link.text.strip() if link else None  # Returns the text inside <a>, if it exists


@tasks.loop(hours=2)
async def scheduled_news_task(bot, api_key, news_config, urls):
    await process_company_news(bot, api_key, news_config, urls)

# Ensure the task is started only if it's not already running
def start_news_task(api_key, news_config, urls):
    if not scheduled_news_task.is_running():
        scheduled_news_task.start(api_key, news_config, urls)