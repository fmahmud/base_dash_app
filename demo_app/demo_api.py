from base_dash_app.apis.api import API
from base_dash_app.enums.http_methods import HttpMethods


class DemoApi(API):
    def __init__(self):
        super().__init__("https://jsonplaceholder.typicode.com")

    @API.endpoint_def("/todos/{todo_id}", HttpMethods.GET.value)
    def test_func(*args, **kwargs):
        print("args = " + str(args))
        print("kwargs = " + str(kwargs))
        return args, kwargs


test_api = DemoApi()
print(test_api.test_func(
    path_params={"{todo_id}": 2}
))