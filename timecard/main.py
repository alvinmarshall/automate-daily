from pprint import pprint
import uuid
import gspread
from PyInquirer import prompt
from examples import custom_style_2
from gspread import Worksheet
from prompt_toolkit.validation import Validator, ValidationError
import json
from datetime import datetime, date, timezone, timedelta
from google.oauth2.service_account import Credentials

SIMPLE_DATE = "%b %d %Y"
SIMPLE_TIME = "%I:%M %p"
SHEET_NAME = 'kelvin-daily'
LAST_SAVED_ROW = 'last_saved_row'
EMAILS = {
    'HR': 'hr@migmeninfo.com',
    'Team Lead': 'benjamin@migmeninfo.com',
    'Self': 'kelvin@migmeninfo.com'
}
SHEET_HEADERS = {
    'DATE': 1,
    'TASK_ID': 2,
    'IN': 3,
    'OUT': 4,
    'ZONE': 5
}


class UUIDValidator(Validator):

    def validate(self, document):
        try:
            uuid.UUID(document.text)
        except ValueError:
            raise ValidationError(message="Please enter a valid ID",
                                  cursor_position=len(document.text))


class StringValidator(Validator):

    def validate(self, document):
        try:
            str(document.text)
        except ValueError:
            raise ValidationError(message="Please enter string value",
                                  cursor_position=len(document.text))


def get_creds() -> Credentials:
    creds: Credentials = Credentials.from_service_account_file("./serviceacct_spreadsheet.json")
    scoped: Credentials = creds.with_scopes([
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ])
    return scoped


def get_utc_date() -> datetime:
    today = datetime.now(timezone.utc)
    utc_time = today.replace(tzinfo=timezone.utc)
    return utc_time.now()


def date_format(current, opt="%b %d %Y"):
    return current.strftime(opt)


client = gspread.authorize(get_creds())
today = date_format(get_utc_date())


def read_json_file(file_path: str):
    try:
        with open(f'{file_path}.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print("failed to load file", e)


def create_task(task_id: str, end: str, zone: str, id: str = str(uuid.uuid4())):
    output = read_json_file(today) or []
    current = get_utc_date()
    task = {
        "id": id,
        "date": date_format(current),
        "task_id": task_id,
        "in": date_format(current, SIMPLE_TIME),
        "out": date_format(current, SIMPLE_TIME),
        "zone": zone
    }
    output.append(task)
    return output


def update_task(data):
    return {
        "id": data[0],
        "date": data[1],
        "task_id": data[2],
        "in": data[3],
        "out": data[4],
        "zone": data[5]
    }


def next_available_row(worksheet):
    str_list = list(filter(None, worksheet.col_values(1)))
    return int(str(len(str_list) + 1))


def insert_sheet_data(worksheet: Worksheet, row, data):
    worksheet.update_cell(row, SHEET_HEADERS['DATE'], data['date'])
    worksheet.update_cell(row, SHEET_HEADERS['TASK_ID'], data['task_id'])
    worksheet.update_cell(row, SHEET_HEADERS['IN'], data['in'])
    worksheet.update_cell(row, SHEET_HEADERS['OUT'], data['out'])
    worksheet.update_cell(row, SHEET_HEADERS['ZONE'], data['zone'])
    print(f"{data['task_id']} --- inserted")


def get_row_index(worksheet: Worksheet):
    last_saved_row = read_text_as_integer(LAST_SAVED_ROW, 3)
    sheet_row_index = next_available_row(worksheet)
    if last_saved_row > sheet_row_index:
        return last_saved_row
    return sheet_row_index + 1


def update_sheet(sheet_name: str, data=[]):
    sheet = client.open(sheet_name)
    worksheet = sheet.sheet1
    last_row = get_row_index(worksheet)
    for i in range(len(data)):
        insert_sheet_data(worksheet, last_row, data[i])
        last_row += 1

    last_row += 1
    write_text_file(LAST_SAVED_ROW, last_row)
    share_option = prompt_share_task_options()
    print("updated sheet")
    if share_option == 'HR':
        sheet.share(EMAILS[share_option], perm_type='user', role='writer')
        print(f'document shared with {EMAILS[share_option]} successfully...')
    elif share_option == 'Self':
        sheet.share(EMAILS[share_option], perm_type='user', role='writer')
        print(f'document shared with {EMAILS[share_option]} successfully...')


def send_task(range_option: str):
    if range_option == 'Today':
        data = read_json_file(today) or []
        if len(data) == 0:
            print("no task to send")
        else:
            update_sheet(SHEET_NAME, data)
    elif range_option == 'Yesterday':
        now = datetime.today()
        yesterday = now - timedelta(days=1)
        data = read_json_file(date_format(yesterday)) or []
        if len(data) == 0:
            print("no task to send")
        else:
            update_sheet(SHEET_NAME, data)


def write_json_file(file_name: str, data):
    with open(f'{file_name}.json', 'w') as f:
        json.dump(data, f)


def write_text_file(file_name: str, data):
    with open(f'{file_name}.txt', 'w') as f:
        f.write(str(data))


def read_text_as_integer(file_name: str, default=0):
    try:
        with open(f'{file_name}.txt', 'r') as f:
            return int(f.read()) or default
    except Exception as e:
        print("file not found...", e)
        return default


def prompt_push_task():
    answer = prompt([
        {
            'type': 'confirm',
            'name': 'exit',
            'message': "Do you want to push today's task ?",
            'default': False,
        },
    ], style=custom_style_2)
    return answer['exit']


def prompt_range_push_task():
    answer = prompt([
        {
            'type': 'confirm',
            'name': 'exit',
            'message': "Do you want to push today's task ?",
            'default': False,
        },
    ], style=custom_style_2)
    return answer['exit']


def prompt_ask_range():
    answer = prompt([{
        'type': 'list',
        'name': 'user_option',
        'message': "Which date task do you want to push?",
        'choices': ["Today", "Yesterday", "Manual"]
    },
    ])
    return answer['user_option']


def prompt_manual():
    answer = prompt([
        {
            'type': "input",
            "name": "now",
            "message": "Enter Date",
            "validate": StringValidator,
            "filter": lambda val: str(val),
            "default": date_format(get_utc_date())
        }
    ])
    return answer['now']


def prompt_create_task():
    answer = prompt([
        {
            'type': "input",
            "name": "task_id",
            "message": "Enter Task ID",
            "validate": StringValidator,
            "filter": lambda val: str(val)
        },
        {
            'type': "input",
            "name": "end",
            "message": "When did your task end? (now/00:00AM)",
            "validate": StringValidator,
            "filter": lambda val: str(val),
            "default": date_format(get_utc_date(), SIMPLE_TIME)
        },
        {
            'type': "input",
            "name": "zone",
            "message": "Your current timezone? (GMT/EST)",
            "validate": StringValidator,
            "filter": lambda val: str(val),
            "default": "GMT"
        }
    ])
    return answer


def prompt_task_unique_idk():
    answer = prompt([
        {
            'type': "input",
            "name": "id",
            "message": "Enter UUID of Task",
            "validate": UUIDValidator,
            "filter": lambda val: str(val)
        }
    ])
    return answer['id']


def prompt_update_task(task):
    data = task[0]
    answer = prompt([
        {
            'type': "input",
            "name": "date",
            "message": "Enter today's date",
            "validate": StringValidator,
            "filter": lambda val: str(val),
            "default": data['date']
        },
        {
            'type': "input",
            "name": "task_id",
            "message": "Enter Task ID",
            "validate": StringValidator,
            "filter": lambda val: str(val),
            "default": data['task_id']
        },
        {
            'type': "input",
            "name": "begin",
            "message": "When did your task start? (now/00:00AM)",
            "validate": StringValidator,
            "filter": lambda val: str(val),
            "default": data['in']
        },
        {
            'type': "input",
            "name": "end",
            "message": "When did your task end? (now/00:00AM)",
            "validate": StringValidator,
            "filter": lambda val: str(val),
            "default": data['out']
        },
        {
            'type': "input",
            "name": "zone",
            "message": "Your current timezone? (GMT/EST)",
            "validate": StringValidator,
            "filter": lambda val: str(val),
            "default": data['zone']
        }
    ])
    return answer


def prompt_task_options():
    answer = prompt([{
        'type': 'list',
        'name': 'user_option',
        'message': "Kelvin's daily timesheet",
        'choices': ["Create", "Read", "Update", "Delete"]
    },
    ])
    return answer['user_option']


def prompt_read_task_options():
    answer = prompt([{
        'type': 'list',
        'name': 'user_option',
        'message': "Read task",
        'choices': ["All", "Today", "Yesterday", "Range"]
    },
    ])
    return answer['user_option']


def prompt_share_task_options():
    answer = prompt([{
        'type': 'list',
        'name': 'user_option',
        'message': "Read task",
        'choices': ["HR", "Self", "Team Lead", "CEO", "Other"],
        'default': 'HR'
    },
    ])
    return answer['user_option']


def get_tasks(id: str = ''):
    if id == '':
        return read_json_file(today)
    return [d for d in read_json_file(today) if d['id'] == id]


def create_task_action():
    create_answer = prompt_create_task()
    task_id = create_answer["task_id"]
    end = create_answer["end"]
    zone = create_answer["zone"]
    task = create_task(task_id, end, zone)
    write_json_file(today, task)


def update_task_action():
    id = prompt_task_unique_idk()
    task = get_tasks(id)
    if len(task) == 0:
        return
    update_answer = prompt_update_task(task)

    date = update_answer["date"]
    task_id = update_answer["task_id"]
    begin = update_answer["begin"]
    end = update_answer["end"]
    zone = update_answer["zone"]

    task_update = update_task([id, date, task_id, begin, end, zone])
    task_list = get_tasks()
    task_index = next((index for (index, d) in enumerate(task_list) if d["id"] == id), None)

    task_list[task_index] = task_update
    write_json_file(today, task_list)


def read_task_action(read_option: str):
    if read_option == 'Today':
        pprint(read_json_file(today))


def main():
    push = prompt_push_task()
    if push:
        range_option = prompt_ask_range()
        send_task(range_option)

    else:
        user_option = prompt_task_options()
        if user_option == 'Create':
            create_task_action()
        elif user_option == 'Read':
            read_option = prompt_read_task_options()
            read_task_action(read_option)

        elif user_option == 'Update':
            update_task_action()

        elif user_option == 'Delete':
            print("Deleting task")


if __name__ == "__main__":
    main()
