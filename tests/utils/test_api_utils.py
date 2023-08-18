import pytest
import requests
from unittest.mock import patch, Mock
from base_dash_app.apis.utils.api_utils import __make_call  # assuming the __make_call function is in 'your_module.py'

# URL for testing
TEST_URL = "http://example.com"

# Expected headers
EXPECTED_HEADERS = {
    'Content-Type': 'application/json',
    'Connection': 'keep-alive'
}


def make_mock_response(status_code=200, json_data=None):
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    return mock_response


def test_successful_request():
    mock_response = make_mock_response(200, {"status": "success"})

    with patch('requests.get', return_value=mock_response) as mock_get:
        response, status_code = __make_call(TEST_URL, requests.get)

        mock_get.assert_called_with(
            url=TEST_URL,
            headers=EXPECTED_HEADERS,
            data=None,
            params={},
            auth=(),
            timeout=200
        )

    assert response == {"status": "success"}
    assert status_code == 200


def test_request_raise_for_status():
    mock_response = make_mock_response(404)
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

    with patch('requests.get', return_value=mock_response):
        with pytest.raises(requests.exceptions.HTTPError):
            __make_call(TEST_URL, requests.get)


def test_connection_error():
    with patch('requests.get', side_effect=requests.exceptions.ConnectionError):
        with pytest.raises(requests.exceptions.ConnectionError):
            __make_call(TEST_URL, requests.get)

# Add more test cases for other exceptions and behaviors as needed
