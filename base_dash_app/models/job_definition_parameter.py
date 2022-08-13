from sqlalchemy import Column, Integer, Sequence, String, orm, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from base_dash_app.models.base_model import BaseModel


TRUES = ["True", "true"]
FALSES = ["False", "false"]


class JobDefinitionParameter(BaseModel):
    __tablename__ = "job_definition_parameters"

    id = Column(Integer, Sequence("job_definition_parameter_id_seq"), primary_key=True)

    job_definition_id = Column(Integer, ForeignKey("job_definitions.id"))
    job_definition = relationship("JobDefinition", back_populates="parameters")

    user_facing_param_name = Column(String)
    variable_name = Column(String)
    is_list = Column(Boolean, default=False)
    param_type_name = Column(String)
    required = Column(Boolean, default=False)
    default_value = Column(String)
    placeholder = Column(String)
    editable = Column(String, default=True)

    def __hash__(self):
        return hash(f"jd-{self.job_definition_id}-param-{self.id}")

    def __init__(self):
        self.param_type = None

    @orm.reconstructor
    def init_on_load(self):
        if self.param_type_name == "str":
            self.param_type = str
        elif self.param_type_name == "int":
            self.param_type = int
        elif self.param_type_name == "float":
            self.param_type = float
        elif self.param_type_name == "bool":
            self.param_type = bool
        else:
            self.param_type = None

    def set_param_type(self, param_type: type, is_list: bool = False):
        if param_type not in [str, int, float, bool]:
            raise Exception(f"Invalid param type: {str(param_type)}")

        self.is_list = bool(is_list)
        self.param_type = param_type
        self.param_type_name = param_type.__name__

    def __lt__(self, other):
        if type(other) != type(self):
            return None

        if self.job_definition_id == other.job_definition_id:
            return self.id < other.id

        return self.job_definition_id < other.job_definition_id

    def __eq__(self, other):
        if type(other) != type(self):
            return False

        return self.user_facing_param_name == other.user_facing_param_name \
            and self.variable_name == other.variable_name \
            and self.is_list == other.is_list \
            and self.param_type_name == other.param_type_name \
            and self.required == other.required \
            and self.default_value == other.default_value \
            and self.placeholder == other.placeholder \
            and self.editable == other.editable \
            and self.variable_name == other.variable_name

    def __repr__(self):
        return self.to_dict()

    def __str__(self):
        pass

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