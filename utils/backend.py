import requests

import settings
from db import Session
from models.token import Token


def api_method_url(method):
    return '{}/{}'.format(settings.JET_BACKEND_API_BASE_URL, method)


def register_token():
    session = Session()
    token = session.query(Token).first()

    if token:
        return token, False

    url = api_method_url('project_tokens/')
    headers = {
        'User-Agent': 'Jet Django'
    }

    r = requests.request('POST', url, headers=headers)
    success = 200 <= r.status_code < 300

    if not success:
        print('Register Token request error', r.status_code, r.reason)
        return None, False

    result = r.json()

    token = Token(token=result['token'].replace('-', ''), date_add=result['date_add'])
    session.add(token)
    session.commit()

    return token, True


def reset_token():
    session = Session()
    session.query(Token).delete()
    session.commit()

    return register_token()


def project_auth(token, permission=None):
    session = Session()
    project_token = session.query(Token).first()

    if not project_token:
        return {
            'result': False
        }

    url = api_method_url('project_auth/')
    data = {
        'project_token': project_token.token,
        'token': token
    }
    headers = {
        'User-Agent': 'Jet Django'
    }

    if permission:
        data.update(permission)

    r = requests.request('POST', url, data=data, headers=headers)
    success = 200 <= r.status_code < 300

    if not success:
        print('Project Auth request error', r.status_code, r.reason)
        return {
            'result': False
        }

    result = r.json()

    if result.get('access_disabled'):
        return {
            'result': False,
            'warning': result.get('warning')
        }

    return {
        'result': True,
        'warning': result.get('warning')
    }
