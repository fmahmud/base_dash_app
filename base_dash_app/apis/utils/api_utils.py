import json
import requests
from requests import HTTPError
import logging
from base_dash_app.apis.utils.request import Request
from base_dash_app.utils.utils import apply

base_json_header = {'Content-Type': 'application/json', 'Connection': 'keep-alive'}
logger = logging.getLogger("APIUtil")


def get_base_header():
    return apply({}, {'Content-Type': 'application/json', 'Connection': 'keep-alive'})


def __make_call(url, func, headers=get_base_header(), body={}, url_params={}, auth=()):
    logger.info('making call to ' + url)
    max_retries = 1
    response = {}
    status_code = 400

    for i in range(max_retries):
        exception = None
        if i > 0:
            logger.info("...retrying")
        try:
            response = func(url=url, headers=headers,
                            data=json.dumps(body), params=url_params, auth=auth, timeout=200)
            if hasattr(response, 'status_code'):
                status_code = response.status_code
            response.raise_for_status()
            break
        except TypeError as e:
            logger.error("TypeError: " + str(e))
            exception = e
            break
        except HTTPError as e:
            logger.error("HTTPError: " + str(response))
            exception = e
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error " + str(e))
            exception = e
        except Exception as e:
            logger.error("General Error " + str(e))
            exception = e

        if i == max_retries:
            raise exception

    return response.json(), status_code


def make_request(call: Request):
    logger.debug("Making request: %s", str(call))
    return __make_call(url=call.url, func=call.method.function,
                headers=call.headers, body=call.body, url_params=call.url_params, auth=call.auth)
