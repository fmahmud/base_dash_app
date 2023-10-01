import os
import ssl

from celery import Celery, Task
from celery.schedules import crontab
from flask import Flask
from kombu.utils.url import as_url


class CelerySingleton:
    _instance = None

    @classmethod
    def get_instance(cls) -> 'CelerySingleton':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if not hasattr(self, "celery"):
            redis_use_ssl = os.getenv("REDIS_USE_SSL", "False").lower() == "true"
            redis_password = os.getenv("REDIS_PASSWORD", "password")
            redis_username = os.getenv("REDIS_USERNAME", "")
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))

            if redis_use_ssl:
                print("CELERY: Using SSL for redis.")
                self.celery_broker_url = as_url(
                    scheme='rediss',  # Note the extra 's', which denotes a secure connection
                    host=redis_host,
                    port=redis_port,
                    password=redis_password,
                    user=redis_username,
                ) + f"0?ssl_cert_reqs=CERT_REQUIRED"

                print(self.celery_broker_url)
                self.broker_use_ssl = {
                    'ssl_cert_reqs': ssl.CERT_REQUIRED
                }
            else:
                self.celery_broker_url = as_url(
                    scheme='redis',
                    host=redis_host,
                    port=redis_port,
                    password=redis_password,
                    user=redis_username,
                ) + "0"
                self.broker_use_ssl = {}

            if self.celery_broker_url is None:
                raise Exception("CELERY_BROKER_URL environment variable not set.")

            class ContextTask(Task):
                def __call__(self, *args, **kwargs):
                    print(f"-- IN CONTEXT TASK: Running task {self.name}.")
                    from base_dash_app.application.runtime_application import RuntimeApplication
                    with RuntimeApplication.get_instance().server.app_context():
                        return self.run(*args, **kwargs)

            self.celery = Celery(
                "Main Celery Instance",
                broker=self.celery_broker_url,
                backend=self.celery_broker_url,
                task_cls=ContextTask,

            )

            self.celery.backend.ensure_chords_allowed()

    def get_celery(self):
        return self.celery

    def update_config(self, app: Flask):
        self.celery.config_from_object(app.config["CELERY"])
        self.celery.set_default()
        app.extensions["celery"] = self.celery


celery = CelerySingleton.get_instance().get_celery()


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    print("============ Setting up periodic tasks.")
    sender.add_periodic_task(
        crontab(minute='*'),
        handle_scheduler_interval.s(),
        name="handle_scheduler_interval"
    )


@celery.task
def handle_scheduler_interval():
    from base_dash_app.application.runtime_application import RuntimeApplication
    RuntimeApplication.get_instance().check_for_scheduled_jobs()
