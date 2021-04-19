# -*- coding: utf-8 -*-

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from discord.ext import commands
from discord_slash import cog_ext as slash
import discord

from config import GOOGLE_API_CREDS

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class Spreadsheet(commands.Cog):
    """Manages caching and browsing through Google Spreadsheets."""

    # TODO: for every entry in database where spreadsheet ID is not null, fetch and cache sheet of every in db;
    #  range will... have to be provided by them (until I can find a solution i guess?)
    def __init__(self, bot):
        self.bot = bot

    @slash.cog_slash(name="sheet", guild_ids=[465910450819694592])
    async def sheet(self, ctx, sheet_id, sheet_range):
        def grab_sheet():
            service = build('sheets', 'v4',
                            credentials=service_account.Credentials.from_service_account_file(
                                GOOGLE_API_CREDS, scopes=SCOPES
                            )
                            )
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=sheet_id,
                                        range=sheet_range).execute()
            return result.get('values', [])

        values = await ctx.bot.loop.run_in_executor(None, grab_sheet)

        await ctx.send(str(values)[:2000])


def setup(bot):
    bot.add_cog(Spreadsheet(bot))
