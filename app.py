import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
import sys
from typing import Optional, Union
import logging
import requests
import time as time_module

load_dotenv()
token = os.getenv("TOKEN")
OWM_API_KEY = os.getenv("OWM_API_KEY")
if not token:
    print("ERROR: TOKEN environment variable is not set.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bot")
start_time = datetime.now(pytz.UTC)
last_roll: dict[int, float] = {}

intents = discord.Intents.default()
intents.members = False
intents.message_content = False
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    if bot.user is None:
        logger.warning("로그인된 사용자 정보가 없습니다.")
    else:
        logger.info(f"로그인됨: {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Slash 명령어 {len(synced)}개 동기화 완료!")
    except Exception as e:
        logger.exception("동기화 오류")

@bot.tree.command(name="ping", description="봇의 응답 속도를 확인합니다.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"응답 속도: {latency}ms")

@bot.tree.command(name="time", description="현재 시간을 표시합니다.")
async def time(interaction: discord.Interaction):
    tz = pytz.timezone("Asia/Seoul")
    now = datetime.now(tz)
    content = f"🕒 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    try:
        await interaction.response.send_message(content)
    except Exception as e:
        logger.exception("time 명령 응답 전송 실패, followup 시도")
        try:
            await interaction.followup.send(content, ephemeral=False)
        except Exception:
            logger.exception("followup 전송도 실패함")

@bot.tree.command(name="say", description="봇이 대신 말합니다.")
@app_commands.describe(text="봇이 대신 말할 내용")
async def say(interaction: discord.Interaction, text: str):
    MAX_BACKTICKS = 0
    backtick_count = text.count("`")
    if backtick_count > MAX_BACKTICKS:
        return await interaction.response.send_message(f"⚠️ 백틱(`)은 최대 {MAX_BACKTICKS}개까지만 사용할 수 있습니다.", ephemeral=True)
    safe_text = text.replace("`", "`\u200b")
    await interaction.response.send_message(f"{safe_text}")

@bot.tree.command(name="uptime", description="봇의 가동 시간을 표시합니다.")
async def uptime(interaction: discord.Interaction):
    delta = datetime.now(pytz.UTC) - start_time
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    await interaction.response.send_message(f"⏱️ 가동 시간: {days}d {hours}h {minutes}m {seconds}s")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    logger.exception("앱 명령 처리 중 오류 발생")
    try:
        await interaction.response.send_message("⚠️ 명령 처리 중 오류가 발생했습니다. 관리자에게 문의하세요.", ephemeral=True)
    except Exception:
        try:
            await interaction.followup.send("⚠️ 명령 처리 중 오류가 발생했습니다. 관리자에게 문의하세요.", ephemeral=True)
        except Exception:
            pass

bot.run(token)