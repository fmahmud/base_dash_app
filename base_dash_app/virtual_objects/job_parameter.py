import uuid
from typing import Type, Union


TRUES = ["True", "true"]
FALSES = ["False", "false"]


class JobParameterDefinition:
    def __init__(
            self,
            param_name: str,
            variable_name: str,
            param_type: Type[Union[str, int, float, bool]],
            is_list: bool = False,
            param_id=None,
            required=False,
            placeholder=None,
            starting_value=None,
            editable=True,
    ):
        self.param_name: str = param_name
        self.param_type: Type[Union[str, int, float, bool]] = param_type
        self.variable_name: str = variable_name
        self.is_list = is_list
        self.param_id = param_id if param_id is not None else uuid.uuid5(
            namespace=uuid.NAMESPACE_X500, name=self.param_name  # X500?
        )
        self.placeholder: str = placeholder if placeholder is not None else self.param_type.__name__
        self.required: bool = required
        self.starting_value = starting_value
        self.editable = editable

    def __hash__(self):
        return hash(self.param_id)

    def __helper_convert_to_type(self, x):
        if self.param_type != str and type(x) == str:
            x = x.replace(" ", "").strip()

        if type(x) != self.param_type:

            if self.param_type == bool:
                if x not in (TRUES + FALSES):
                    raise Exception("Invalid input for type boolean.")
                else:
                    x = x in TRUES
            else:
                x = self.param_type(x)
        return x

    def convert_to_correct_type(self, user_input):
        if self.is_list:
            to_return = []
            input_split = user_input.split(",")
            for x in input_split:
                to_return.append(self.__helper_convert_to_type(x))

            return to_return
        else:
            return self.__helper_convert_to_type(user_input)
