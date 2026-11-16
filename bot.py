import io
import os
import aiohttp
import discord
from discord import app_commands

TOKEN = os.environ["DISCORD_TOKEN"]
SILVER = discord.Color.from_str("#C0C0C0")
DARK_GREY = discord.Color.from_str("#4A4A4A")
BOT_NAME = "Batas Nyata"
STATUS_TEXT = "Created Apin Studio"
MAX_SIZE = 25 * 1024 * 1024

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def make_embed(title, desc, color=SILVER):
    e = discord.Embed(title=title, description=desc, color=color)
    e.set_footer(text=f"{BOT_NAME} • {STATUS_TEXT}")
    return e


def detect_ext(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "png"
    if data.startswith(b"\xff\xd8"):
        return "jpg"
    if data.startswith(b"OggS"):
        return "ogg"
    if data.startswith(b"ID3") or data[:2] == b"\xff\xfb":
        return "mp3"
    if data.startswith(b"version"):
        return "mesh"
    if data.startswith(b"<roblox"):
        return "rbxm"
    return "bin"


@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(
        activity=discord.CustomActivity(name=STATUS_TEXT),
        status=discord.Status.idle,
    )
    print(f"Login sebagai {client.user}")


@tree.command(name="asset", description="Download asset Roblox dari asset ID")
@app_commands.describe(asset_id="ID asset Roblox")
async def asset(interaction: discord.Interaction, asset_id: int):
    await interaction.response.defer()
    url = f"https://assetdelivery.roblox.com/v2/assetId/{asset_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status != 200:
                return await interaction.followup.send(
                    embed=make_embed("Gagal", "Asset tidak ditemukan atau tidak bisa diakses.", DARK_GREY)
                )
            data = await r.json()

        try:
            location = data["locations"][0]["location"]
        except (KeyError, IndexError):
            return await interaction.followup.send(
                embed=make_embed("Gagal", "Asset ini privat atau tidak punya file yang bisa diunduh.", DARK_GREY)
            )

        async with session.get(location) as f:
            content = await f.read()

    if len(content) > MAX_SIZE:
        return await interaction.followup.send(
            embed=make_embed("Gagal", "File terlalu besar untuk dikirim lewat Discord.", DARK_GREY)
        )

    ext = detect_ext(content)
    filename = f"{asset_id}.{ext}"
    embed = make_embed(
        "Asset Berhasil Diunduh",
        f"**Asset ID:** `{asset_id}`\n**Tipe file:** `.{ext}`\n**Ukuran:** `{len(content)/1024:.1f} KB`",
    )
    await interaction.followup.send(embed=embed, file=discord.File(io.BytesIO(content), filename=filename))


client.run(TOKEN)
