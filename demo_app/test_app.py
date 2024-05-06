

from base_dash_app.application.celery_decleration import CelerySingleton
from base_dash_app.application.runtime_application import RuntimeApplication
from demo_app.app_descriptor import my_app_descriptor

celery_singleton: CelerySingleton = CelerySingleton.get_instance()
celery = celery_singleton.get_celery()

rta = RuntimeApplication(my_app_descriptor)
app = rta.app
server = rta.server
server.config["TESTING"] = True

