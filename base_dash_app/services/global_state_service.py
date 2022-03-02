from typing import Dict, Hashable, Any, Type

from base_dash_app.services.base_service import BaseService, T


class GlobalStateService(BaseService):
    def __init__(self, initial_state: Dict[Hashable, Any] = None):
        super().__init__(dbm=None, service_name="GlobalStateService", object_type=Type[T])
        self.state: Dict[Hashable, Any] = initial_state if initial_state is not None else {}
