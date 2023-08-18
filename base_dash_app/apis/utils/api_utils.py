import json
import traceback
from json import JSONDecodeError
from typing import Callable

import requests
from requests import HTTPError
import logging
from base_dash_app.apis.utils.request import Request
from base_dash_app.utils.utils import apply

base_json_header = {'Content-Type': 'application/json', 'Connection': 'keep-alive'}
logger = logging.getLogger("APIUtil")


def get_base_header():
    return apply({}, {'Content-Type': 'application/json', 'Connection': 'keep-alive'})


MAX_RETRIES = 1
TIMEOUT = 200


def __make_call(
        url, request_function: Callable, headers=None, body=None,
        url_params=None, auth=(), timeout=TIMEOUT,
        parse_json=True
):
    """
    Make an HTTP call to the specified URL and handle potential errors.

    Parameters:
    ----------
    url : str
        The URL endpoint to which the request will be made.

    request_function : callable
        The HTTP method function to call, e.g., requests.get or requests.post.

    headers : dict, optional (default: result of get_base_header())
        A dictionary of headers to send with the request.

    body : dict, optional (default: {})
        A dictionary representing the request payload/body.

    url_params : dict, optional (default: {})
        A dictionary representing the URL parameters to append to the URL.

    auth : tuple, optional (default: ())
        A tuple containing the username and password for HTTP Basic Authentication.

    timeout : int, optional (default: 200)
        The request timeout in seconds.

    parse_json : bool, optional (default: True)
        A flag indicating whether the response should be parsed as JSON or returned as raw text.

    Returns:
    -------
    tuple
        A tuple containing the JSON-decoded response (or raw text if parse_json is False) and the HTTP status code.

    Raises:
    ------
    TypeError, HTTPError, requests.exceptions.ConnectionError, json.JSONDecodeError, Exception
        Any exceptions raised during the HTTP call or response processing will be caught and logged. If the request
        fails after the max number of retries, the caught exception will be raised.

    Notes:
    -----
    The function will log and retry on certain exceptions, and will break out of the retry loop on others.
    """
    if headers is None:
        headers = get_base_header()
    if body is None:
        body = {}
    if url_params is None:
        url_params = {}

    logger.info('making call to ' + url)

    exception = None
    response_json = {}
    status_code = 400
    response = None

    for i in range(MAX_RETRIES + 1):  # Adjust to ensure loop runs for MAX_RETRIES times
        if i > 0:
            logger.info("...retrying")

        try:
            response = request_function(
                url=url, headers=headers,
                data=None if body == {} else json.dumps(body),
                params=url_params, auth=auth, timeout=timeout
            )
            status_code = response.status_code
            response.raise_for_status()

            if parse_json:
                response_json = response.json()
            else:
                response_json = response.text
            return response_json, status_code

        except (TypeError, HTTPError, requests.exceptions.ConnectionError, JSONDecodeError, Exception) as error:
            if logger.level == logging.DEBUG:
                traceback.print_exc()
            logger.error(f"Error: {type(error).__name__} - {str(error)}")
            exception = error
            # If it's not a connection error, no need to retry
            if not isinstance(e, requests.exceptions.ConnectionError):
                break

    raise exception


def make_request(call: Request, parse_json=True):
    logger.debug("Making request: %s", str(call))
    return __make_call(
        url=call.url, request_function=call.method.function,
        headers=call.headers, body=call.body, url_params=call.query_params,
        auth=call.auth, timeout=call.timeout, parse_json=parse_json
    )
