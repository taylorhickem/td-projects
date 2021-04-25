'''Created on 2021-04-24
@author: Taylor W Hickem
'''
# useful info https://developer.todoist.com/
# ---------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------
import pandas as pd
import datetime as dt
import copy
import sys

import database as db
import api

from sqlalchemy import create_engine, MetaData

# ---------------------------------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------------------------------
UI_SHEET = 'projects'


# ---------------------------------------------------------------------------------------------------
# DYNAMIC
# ---------------------------------------------------------------------------------------------------
UI_CONFIG = {}
DB = {}
tables = {}


# ---------------------------------------------------------------------------------------------------
# LIBRARIES
# ---------------------------------------------------------------------------------------------------
FIELDS = {
    'projects': {
        'id': int,
        'name': str,
        'comment_count': int,
        'order': int,
        'parent_id': int
    },
    'tasks': {
        'id': int,
        'parent_id': int,
        'section_id': int,
        'project_id': int,
        'label_ids': str,
        'content': str,
        'comment_count': int,
        'order': int,
        'priority': int,
        'completed': bool,
        'created': dt.date,
        'due': str
    }
}


# ---------------------------------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------------------------------
def update():
    load()
    sync_db()
    post_ui()


def load():
    db.load()
    load_config()
    load_db()


def sync_db():
    global tables
    tables['projects'] = get_item_table('projects')
    update_table(tables['projects'], 'project', False)

    tables['tasks'] = get_item_table('tasks')
    task_tbl = copy.deepcopy(tables['tasks'])
    task_tbl['label_ids'] = task_tbl['label_ids'].astype(FIELDS['tasks']['label_ids'])
    task_tbl['due'] = task_tbl['due'].astype(FIELDS['tasks']['due'])
    update_table(task_tbl, 'task', False)


def load_db():
    global DB
    db.load()
    DB['con'] = db.create_engine(db.CONFIG['db_path'], echo=False)
    DB['inspector'] = db.Inspector.from_engine(DB['con'])
    DB['table_names'] = DB['inspector'].get_table_names()
    DB['metadata'] = MetaData(bind=DB['con'])
    DB['metadata'].reflect()


def load_config():
    ''' loads gsheet user interface config
    '''
    global UI_CONFIG
    config_tbl = db.get_sheet(UI_SHEET, 'config')
    UI_CONFIG = get_reporting_config(config_tbl)


def get_reporting_config(tbl):
    DATE_FORMAT = '%Y-%m-%d'
    config = {}
    groups = list(tbl['group'].unique())
    for grp in groups:
        group_tbl = tbl[tbl['group'] == grp][['parameter', 'value', 'data_type']]
        params = dict(group_tbl[['parameter', 'value']]
                      .set_index('parameter')['value'])
        data_types = dict(group_tbl[['parameter', 'data_type']]
                          .set_index('parameter')['data_type'])
        for p in params:
            data_type = data_types[p]
            if ~(data_type == 'str'):
                if ~pd.isnull(params[p]):
                    if data_type in db.NUMERIC_TYPES:
                        numStr = params[p]
                        if numStr == '':
                            numStr = '0'
                        if data_type == 'int':
                            params[p] = int(numStr)
                        elif data_type == 'float':
                            params[p] = float(numStr)
                    elif data_type == 'date':
                        params[p] = dt.datetime.strptime(params[p], DATE_FORMAT).date()
        config[grp] = params
    return config


# -----------------------------------------------------
# SQL database
# -----------------------------------------------------


def table_exists(table_name):
    return table_name in DB['table_names']


def get_table(table_name):
    if table_exists(table_name):
        tbl = pd.read_sql_table(table_name, con=DB['con'])
    else:
        tbl = None
    return tbl


def update_table(tbl, table_name, append=True):
    if append:
        ifex = 'append'
    else:
        ifex = 'replace'
    tbl.to_sql(table_name, con=DB['con'], if_exists=ifex, index=False)


# ---------------------------------------------------------------------------------------------------
# gsheet
# ---------------------------------------------------------------------------------------------------
def post_ui():
    project_tbl = get_table('project').fillna('')
    db.post_to_gsheet(project_tbl, UI_SHEET, 'projects', input_option='USER_ENTERED')

    task_tbl = get_table('task').fillna('')
    db.post_to_gsheet(task_tbl, UI_SHEET, 'tasks', input_option='USER_ENTERED')

# ----------------------------------------------------------------------------------------------
# Projects
# ----------------------------------------------------------------------------------------------
def get_item_table(item_type='projects'):
    fields = list(FIELDS[item_type].copy().keys())
    items = api.get_items(item_type)
    tbl = pd.DataFrame.from_records(items)[fields]
    return tbl


# -----------------------------------------------------
# Command line interface
# -----------------------------------------------------
def autorun():
    if len(sys.argv) > 1:
        process_name = sys.argv[1]
        if process_name == 'update':
            update()
    else:
        print('no report specified')


if __name__ == "__main__":
    autorun()


# ----------------------------------------------------------------------------------------------
# END
# ----------------------------------------------------------------------------------------------