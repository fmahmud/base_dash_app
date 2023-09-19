

class ComponentInstanceNotFoundException(Exception):
    """Raised when a component instance is not found in the component registry."""

    def __init__(self, cls_name: str, instance_id: int):
        super().__init__(f"Component of type {cls_name} with instance id {instance_id} was not found.")
