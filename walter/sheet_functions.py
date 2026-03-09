import asyncio
import os
import gspread
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def parse_us_date(date_str):
    date_str.strip()
    if not date_str:
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def read_weekly_events():
    gc = gspread.service_account(filename=os.environ["GOOGLE_SHEETS_JSON_DIR"])
    sheet = gc.open_by_key(os.environ["GOOGLE_SHEETS_KEY"]).worksheet("Events")

    row_list = sheet.batch_get(["A2:E100"])[0]

    valid_events = []
    curr_date = datetime.now().date()
    for row in row_list:
        if not row:
            continue
        if len(row) < 5:
            row = row + [""] * (5 - len(row))
        event_date = parse_us_date(row[1])
        if event_date is None:
            continue
        if curr_date <= event_date <= curr_date + timedelta(days=6):
            valid_events.append(row)
    
    return valid_events

async def read_weekly_events_async():
    return await asyncio.to_thread(read_weekly_events)

def get_agenda():
    gc = gspread.service_account(filename=os.environ["GOOGLE_SHEETS_JSON_DIR"])
    sheet = gc.open_by_key(os.environ["GOOGLE_SHEETS_KEY"]).worksheet("Agenda")

    row_list = sheet.batch_get(["A2:F100"])[0]

    valid_agenda = []
    curr_date = datetime.now().date()
    for row in row_list:
        if not row:
            continue

        if len(row) < 6:
            row = row + [""] * (6 - len(row))
    
        event_date = parse_us_date(row[1])
        if event_date is None:
            continue

        status = row[4].strip().lower()
        if curr_date - timedelta(days=7) <= event_date <= curr_date + timedelta(days=30) and status != "complete":
            valid_agenda.append(row)
    return valid_agenda

async def read_agenda_async():
    return await asyncio.to_thread(get_agenda)

def write_question(sheet_name, question):
    gc = gspread.service_account(filename=os.environ["GOOGLE_SHEETS_JSON_DIR"])
    sheet = gc.open_by_key(os.environ["GOOGLE_SHEETS_KEY"]).worksheet(sheet_name)

    curr_date = datetime.now().date()
    col_list = sheet.batch_get(["B2:J5"], major_dimension="COLUMNS")[0]
    for i in range(len(col_list)):
        col_date = parse_us_date(col_list[i][0])
        if col_date > curr_date:
            
            # add 2 because cells start at B
            # row updated in sheet is 5
            if len(col_list[i]) == 3: 
                sheet.update_cell(5, i + 2, question)
            else:
                curr_questions = col_list[i][3]
                sheet.update_cell(5, i + 2, curr_questions + ", " + question)
            break

async def write_question_async(sheet_name, question):
    return await asyncio.to_thread(write_question, sheet_name, question)


    
    
if __name__ == "__main__":
    pass