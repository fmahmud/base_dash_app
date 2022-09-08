import time

from base_dash_app.apis.api import API
from base_dash_app.enums.http_methods import HttpMethods


class DemoApi(API):
    def __init__(self, *args, **kwargs):
        super().__init__("https://jsonplaceholder.typicode.com", **kwargs)

    @API.endpoint_def("/todos/{todo_id}", HttpMethods.GET.value, timeout=1)
    def test_func(*args, **kwargs):
        print("args = " + str(args))
        print("kwargs = " + str(kwargs))
        return args
