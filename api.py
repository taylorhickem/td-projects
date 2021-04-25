'''Created on 2021-04-24
@author: Taylor W Hickem
'''
# useful info https://developer.todoist.com/
# ---------------------------------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------------------------------
import requests, uuid, json

# ---------------------------------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------------------------------
USER_TOKEN = 'df0a9ed8cfa22909d85674d43696c068ceee894c'
REQUEST_URL = 'https://api.todoist.com/rest/v1/'

# ---------------------------------------------------------------------------------------------------
# LIBRARIES
# ---------------------------------------------------------------------------------------------------
todo_classes = {
    'projects': {
        'request_key': 'projects'
    },
    'tasks': {
        'request_key': 'tasks'
    },
    #doesn't work for bulk requests but may work for task-specific request
    'comments': {
        'request_key': 'comments'
    },
    'labels': {
        'request_key': 'labels'
    }
}


# ---------------------------------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------------------------------
def get_items(item_type='projects'):
    response = requests.get(
        REQUEST_URL + todo_classes[item_type]['request_key'],
        headers={
            'Authorization': 'Bearer ' + USER_TOKEN
        }).json()
    return response


def save_items_to_json(item_type='projects'):
    data = get_items(item_type)
    with open(item_type + '.json', 'w') as f:
        json.dump(data, f)


# ---------------------------------------------------------------------------------------------------