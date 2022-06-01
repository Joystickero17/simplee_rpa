from typing import Dict, Optional
from requests import request
from requests.exceptions import HTTPError, RequestException
import logging
import json
import os
HEADERS = {
    'Content-Type': 'application/json',
    'Api-Token': os.getenv('ACTIVE_CAMPAING_TOKEN', '')
}
BASE_URL = os.getenv('ACTIVE_CAMPAING_URL', '')


def sync_contact(
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        fields: Optional[Dict] = [], *args, **kwargs):
    url = f"{BASE_URL}/contact/sync"
    data = {
        "contact": {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "phone": phone,
            "fieldValues": fields
        }
    }
    try:
        result = request(
            'POST',
            url,
            data=json.dumps(data),
            headers=HEADERS)

        if result.status_code in [200, 201]:
            logging.debug(f'sync_contact: {result.json()}')
            return result.json()
    except HTTPError as e:
        logging.error(f'sync_contact: {e}')
    except RequestException as e:
        logging.exception(f'sync_contact: {e}')
    return None


def add_tag_to_contact(contact_id: int, tag_id: int, *args, **kwargs):

    url = f"{BASE_URL}/contactTags"
    data = {
        "contactTag": {
            "contact": contact_id,
            "tag": tag_id
        }
    }
    try:
        result = request(
            'POST',
            url,
            data=json.dumps(data),
            headers=HEADERS)
        if result.status_code in [200, 201]:
            logging.debug(f'add_tag_to_contact: {result.json()}')
            return result.json()
    except HTTPError as e:
        logging.error(f'add_tag_to_contact: {e}')
    except RequestException as e:
        logging.exception(f'add_tag_to_contact: {e}')
    return None


def suscribe_to_list(contact_id: int, list_id: int, *args, **kwargs):
    url = f"{BASE_URL}/contactLists"
    data = {
        "contactList": {
            "list": list_id,
            "contact": contact_id,
            "status": 1
        }
    }
    try:
        result = request(
            'POST',
            url,
            data=json.dumps(data),
            headers=HEADERS
        )
        if result.status_code in [200, 201]:
            logging.debug(f'suscribe_to_list: {result.json()}')
            return result.json()
    except HTTPError as e:
        logging.error(f'suscribe_to_list: {e}')
    except RequestException as e:
        logging.exception(f'suscribe_to_list: {e}')
    return None
