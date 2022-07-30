

class EnvVarDefinition:
    def __init__(self, name: str, var_type: type, required: bool = False):
        self.name: str = name
        self.var_type: type = var_type
        self.required: bool = required
        self.value = None
