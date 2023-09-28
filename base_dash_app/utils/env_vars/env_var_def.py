

class EnvVarDefinition:
    def __init__(self, name: str, var_type: type, required: bool = False):
        self.name: str = name
        self.var_type: type = var_type
        self.required: bool = required
        self.value = None

    def __repr__(self):
        return f"{self.name}={self.value}({self.var_type}, {self.required})"

    def __str__(self):
        return self.__repr__()
