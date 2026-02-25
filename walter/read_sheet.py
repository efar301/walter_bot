import asyncio
import os
import gspread
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def read_weekly_events():
    gc = gspread.service_account(filename=os.environ["GOOGLE_SHEETS_JSON_DIR"])
    sheet = gc.open_by_key(os.environ["GOOGLE_SHEETS_KEY"]).worksheet("Events")

    row_list = sheet.batch_get(["A2:E100"])[0]

    valid_events = []
    curr_date = datetime.now().date()
    for row in row_list:
        if len(row) < 2:
            continue
        try:
            event_date = datetime.strptime(row[1], "%m/%d/%Y").date()
        except ValueError:
            continue
        if curr_date <= event_date <= curr_date + timedelta(days=7):
            valid_events.append(row)
    
    return valid_events

async def read_weekly_events_async():
    return await asyncio.to_thread(read_weekly_events)

def get_agenda():
    gc = gspread.service_account(filename=os.environ["GOOGLE_SHEETS_JSON_DIR"])
    sheet = gc.open_by_key(os.environ["GOOGLE_SHEETS_KEY"]).worksheet("Agenda")

    row_list = sheet.batch_get(["A2:D100"])[0]

    valid_agenda = []
    curr_date = datetime.now().date()
    for row in row_list:
        if len(row) < 1:
            continue
    
        try:
            event_date = datetime.strptime(row[1], "%m/%d/%Y").date()
        except ValueError:
            continue

        if curr_date - timedelta(days=7) <= event_date <= curr_date + timedelta(days=30):
            valid_agenda.append(row)

    return valid_agenda

async def read_agenda_async():
    return await asyncio.to_thread(get_agenda)





if __name__ == "__main__":
    read_weekly_events()
