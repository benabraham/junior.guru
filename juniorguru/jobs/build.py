import os
import json
from pathlib import Path

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from jinja2 import Template


SRC_DIR = Path(__file__).parent
BUILD_DIR = Path(__file__).parent.parent.parent / 'build'


google_service_account_path = SRC_DIR / 'google_service_account.json'
google_service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT') or google_service_account_path.read_text()
google_service_account = json.loads(google_service_account_json)
google_scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_service_account, google_scope)


doc_key = '1TO5Yzk0-4V_RzRK5Jr9I_pF5knZsEZrNn2HKTXrHgls'
doc = gspread.authorize(credentials).open_by_key(doc_key)
table = doc.worksheet('jobs').get_all_values()


jobs = [row[0] for row in table]
data = dict(name='Honza', jobs=jobs)


template_path = SRC_DIR / 'template.html'
template = Template(template_path.read_text())

(BUILD_DIR / 'jobs').mkdir()
html_path = BUILD_DIR / 'jobs' / 'index.html'
html_path.write_text(template.render(**data))
