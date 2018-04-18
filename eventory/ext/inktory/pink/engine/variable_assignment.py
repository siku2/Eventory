from .object import Object


class VariableAssignment(Object):
    variable_name: str
    is_new_declaration: bool
    is_global: bool

    def __init__(self, variable_name: str = None, is_new_declaration: bool = False):
        self.variable_name = variable_name
        self.is_new_declaration = is_new_declaration
        self.is_global = False

    def __str__(self) -> str:
        return f"VarAssign to {self.variable_name}"
