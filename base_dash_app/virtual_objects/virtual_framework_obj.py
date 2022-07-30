
class VirtualFrameworkObject:
    def __init__(self, *args, **kwargs):
        self.dbm = kwargs["dbm"] if "dbm" in kwargs else None
        self.get_service = kwargs["service_provider"] if "service_provider" in kwargs else None
        self.get_api = kwargs["api_provider"] if "api_provider" in kwargs else None
        self.all_apis = kwargs["all_apis"] if "all_apis" in kwargs else None
        self.register_callback_func = kwargs["register_callback_func"] if "register_callback_func" in kwargs else None
        self.push_alert = kwargs["push_alert"] if "push_alert" in kwargs else None
        self.remove_alert = kwargs["remove_alert"] if "remove_alert" in kwargs else None
        self.env_vars = kwargs["env_vars"] if "env_vars" in kwargs else None
