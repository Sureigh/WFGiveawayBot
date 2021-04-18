# -*- coding: utf-8 -*-

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from discord.ext import commands
import discord

from config import GOOGLE_API_CREDS

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class Spreadsheet(commands.Cog):
    """Manages caching and browsing through Google Spreadsheets."""

    # TODO: for every entry in database where spreadsheet ID is not null, fetch and cache sheet of every in db;
    #  range will... have to be provided by them (until I can find a solution i guess?)
    def __init__(self, bot):
        self.bot = bot

        def grab_sheet(guild_id):
            service = build('sheets', 'v4', credentials=Credentials.from_authorized_user_file(GOOGLE_API_CREDS, SCOPES))
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=bot.sheet_id(guild_id),
                                        range=bot.sheet_range(guild_id)).execute()
            values = result.get('values', [])

        bot.loop.run_in_executor(None, grab_sheet)


def setup(bot):
    bot.add_cog(Spreadsheet(bot))
