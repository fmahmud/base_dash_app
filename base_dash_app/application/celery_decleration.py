import os

from celery import Celery, Task
from celery.schedules import crontab
from flask import Flask


class CelerySingleton:
    _instance = None

    @classmethod
    def get_instance(cls) -> 'CelerySingleton':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if not hasattr(self, "celery"):
            celery_broker_url = os.getenv("CELERY_BROKER_URL")

            if celery_broker_url is None:
                raise Exception("CELERY_BROKER_URL environment variable not set.")

            class ContextTask(Task):
                def __call__(self, *args, **kwargs):
                    print(f"-- IN CONTEXT TASK: Running task {self.name}.")
                    from base_dash_app.application.runtime_application import RuntimeApplication
                    with RuntimeApplication.get_instance().server.app_context():
                        return self.run(*args, **kwargs)

            self.celery = Celery(
                "Main Celery Instance",
                broker=celery_broker_url,
                backend=celery_broker_url,
                task_cls=ContextTask
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
