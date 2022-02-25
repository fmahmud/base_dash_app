from typing import List, Type

from base_dash_app.services.base_service import BaseService
from base_dash_app.views.base_view import BaseView


class AppDescriptor:
    """
    Used to define the service with as much granular control as needed.
    """
    def __init__(
        self, *,
            title: str = None,
            service_classes: List[Type[BaseService]] = None,
            external_stylesheets: List[str] = None,
            views: List[Type[BaseView]] = None,
            db_file: str = None,
    ):
        """
        :param db_file: Optional - location of an sqlite db file
        :param title: Optional - Title of app
        :param service_classes: Optional - list of all uninitialized service classes that extend BaseService
        :param external_stylesheets:
        :param views: Optional - List of all uninitialized view classes that extend BaseView that could be rendered in
            the app
        """

        self.db_file: str = db_file
        self.title: str = title if title is not None else ""
        self.service_classes: List[Type[BaseService]] = service_classes if service_classes is not None else []
        self.external_stylesheets: List[str] = external_stylesheets if external_stylesheets is not None else []
        self.views: List[Type[BaseView]] = views if views is not None else []