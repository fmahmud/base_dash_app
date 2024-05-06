import time

from base_dash_app.application.runtime_application import RuntimeApplication
from demo_app.app_descriptor import my_app_descriptor

time.sleep(10)


from base_dash_app.application.celery_decleration import CelerySingleton

celery_singleton: CelerySingleton = CelerySingleton.get_instance()
celery = celery_singleton.get_celery()

rta = RuntimeApplication(my_app_descriptor)
rta.celery = celery
app = rta.app
server = rta.server
db_manager = rta.dbm
