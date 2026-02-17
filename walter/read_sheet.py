import asyncio
import os
import gspread
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

gc = gspread.service_account(filename=os.environ["GOOGLE_SHEETS_JSON_DIR"])

def read_weekly_events():
    sheet = gc.open_by_key(os.environ["GOOGLE_SHEETS_KEY"]).worksheet("Events")

    row_list = sheet.batch_get(["A2:E100"])[0]

    valid_events = []
    curr_date = datetime.now()
    for row in row_list:
        event_date = datetime.strptime(row[1], "%m/%d/%Y")
        if curr_date <= event_date <= curr_date + timedelta(days=7):
            valid_events += row
    
    return(valid_events)

async def read_weekly_events_async():
    return await asyncio.to_thread(read_weekly_events)





if __name__ == "__main__":
    read_weekly_events()