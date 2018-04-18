from typing import Any, Dict, List, Optional

from .choice import Choice
from .choice_point import ChoicePoint
from .container import Container
from .control_command import CommandType, ControlCommand
from .divert import Divert
from .glue import Glue
from .ink_list import InkList, InkListItem
from .list_definition import ListDefinition
from .list_definition_origin import ListDefinitionOrigin
from .native_function_call import NativeFunctionCall
from .object import Object
from .path import Path
from .push_pop import PushPopType
from .tag import Tag
from .value import DivertTargetValue, FloatValue, IntValue, ListValue, StringValue, Value, VariablePointerValue
from .variable_assignment import VariableAssignment
from .variable_reference import VariableReference
from .void import Void


class Json:
    _control_command_names: List[str] = [None] * CommandType.TOTAL_VALUES

    @staticmethod
    def list_to_jarray(serialisables: List[Object]) -> List[Any]:
        j_array = []
        for s in serialisables:
            j_array.append(Json.runtime_object_to_j_token(s))
        return j_array

    @staticmethod
    def j_array_to_runtime_obj_list(j_array: List[Any], skip_last: bool = False) -> List[Object]:
        count = len(j_array)
        if skip_last:
            count -= 1
        _list = []
        for i in range(count):
            j_tok = j_array[i]
            runtime_obj = Json.j_token_to_runtime_object(j_tok)
            _list.append(runtime_obj)
        return _list

    @staticmethod
    def dictionary_runtime_objs_to_j_object(dictionary: Dict[str, Object]) -> Dict[str, Any]:
        json_obj = {}
        for key, value in dictionary.items():
            if value:
                json_obj[key] = Json.runtime_object_to_j_token(value)
        return json_obj

    @staticmethod
    def j_object_to_dictionary_runtime_objs(j_object: Dict[str, Any]) -> Dict[str, Object]:
        dictionary = {}
        for key, value in j_object.items():
            dictionary[key] = Json.j_token_to_runtime_object(value)
        return dictionary

    @staticmethod
    def j_object_to_int_dictionary(j_object: Dict[str, Any]) -> Dict[str, int]:
        dictionary = {}
        for key, value in j_object.items():
            dictionary[key] = int(value)
        return dictionary

    @staticmethod
    def int_dictionary_to_j_object(dictionary: Dict[str, int]) -> Dict[str, Any]:
        """This function is utterly pointless in Python but eh"""
        j_obj = {}
        for key, value in dictionary:
            j_obj[key] = value
        return j_obj

    @staticmethod
    def j_token_to_runtime_object(token: Any) -> Optional[Object]:
        if isinstance(token, (int, float)):
            return Value.create(token)
        if isinstance(token, str):
            string = token
            first_char = string[0]
            if first_char == "^":
                return StringValue(string[1:])
            elif first_char == "\n" and len(string) == 1:
                return StringValue("\n")
            if str == "<>":
                return Glue()
            for i in range(len(Json._control_command_names)):
                cmd_name = Json._control_command_names[i]
                if string == cmd_name:
                    return ControlCommand(CommandType(i))
            if string == "L^":
                string = "^"
            if NativeFunctionCall.CallExistsWithName(string):
                return NativeFunctionCall.CallWithName(string)
            if string == "->->":
                return ControlCommand.PopTunnel
            elif string == "~ret":
                return ControlCommand.PopFunction
            if string == "void":
                return Void()
        if isinstance(token, dict):
            obj = token
            prop_value = obj.get("^->")
            if prop_value:
                return DivertTargetValue(Path(prop_value))
            prop_value = obj.get("^var")
            if prop_value:
                var_ptr = VariablePointerValue(prop_value)
                prop_value = obj.get("ci")
                if prop_value:
                    var_ptr.context_index = int(prop_value)
                return var_ptr

            is_divert = False
            pushes_to_stack = False
            div_push_type = PushPopType.Function
            external = False
            if "f()" in obj:
                prop_value = obj["f()"]
                is_divert = True
                pushes_to_stack = True
                div_push_type = PushPopType.Function
            elif "->t->" in obj:
                prop_value = obj["->t->"]
                is_divert = True
                pushes_to_stack = True
                div_push_type = PushPopType.Tunnel
            elif "x()" in obj:
                prop_value = obj["x()"]
                is_divert = True
                external = True
                pushes_to_stack = False
                div_push_type = PushPopType.Function
            if is_divert:
                divert = Divert()
                divert.pushes_to_stack = pushes_to_stack
                divert.stack_push_type = div_push_type
                divert.is_external = external
                target = str(prop_value)
                if "var" in obj:
                    divert.variable_divert_name = target
                else:
                    divert.target_path_string = target
                divert.is_conditional = "c" in obj
                if external:
                    if "exArgs" in obj:
                        divert.external_args = int(obj["exArgs"])
                return divert
            if "*" in obj:
                choice = ChoicePoint()
                choice.path_string_on_choice = str(obj["*"])
                if "flg" in obj:
                    choice.flags = int(obj["flg"])
                return choice
            if "VAR?" in obj:
                return VariableReference(str(obj["VAR?"]))
            elif "CNT?" in obj:
                read_count_var_ref = VariableReference()
                read_count_var_ref.path_string_for_count = str(obj["CNT?"])
                return read_count_var_ref

            is_var_ass = False
            is_global_var = False
            if "VAR=" in obj:
                prop_value = obj["VAR="]
                is_var_ass = True
                is_global_var = True
            elif "temp=" in obj:
                prop_value = obj["temp="]
                is_var_ass = True
                is_global_var = False
            if is_var_ass:
                var_name = str(prop_value)
                is_new_decl = "re" not in obj
                var_ass = VariableAssignment(var_name, is_new_decl)
                var_ass.is_global = is_global_var
                return var_ass
            if "#" in obj:
                return Tag(str(obj["#"]))
            if "list" in obj:
                list_content = obj["list"]
                raw_list = InkList()
                if "origins" in obj:
                    raw_list.set_initial_origin_names(obj["origins"])
                for key, value in list_content.items():
                    item = InkListItem(key)
                    raw_list[item] = value
                return ListValue(raw_list)
            if obj["originalChoicePath"]:
                return Json.j_object_to_choice(obj)
        if isinstance(token, list):
            return Json.j_array_to_container(token)
        if token is None:
            return None
        raise Exception(f"Failed to convert token to runtime object: {token}")

    @staticmethod
    def runtime_object_to_j_token(obj: Object) -> Any:
        if isinstance(obj, Container):
            return Json.container_to_j_array(obj)
        if isinstance(obj, Divert):
            div_type_key = "->"
            if obj.is_external:
                div_type_key = "x()"
            elif obj.pushes_to_stack:
                if obj.stack_push_type == PushPopType.Function:
                    div_type_key = "f()"
                elif obj.stack_push_type == PushPopType.Tunnel:
                    div_type_key = "->t->"
            if obj.has_variable_target:
                target_str = obj.variable_divert_name
            else:
                target_str = obj.target_path_string
            j_obj = {}
            j_obj[div_type_key] = target_str
            if obj.has_variable_target:
                j_obj["var"] = True
            if obj.is_conditional:
                j_obj["c"] = True
            if obj.external_args > 0:
                j_obj["exArgs"] = obj.external_args
            return j_obj

        if isinstance(obj, ChoicePoint):
            j_obj = {}
            j_obj["*"] = obj.path_string_on_choice
            j_obj["flg"] = obj.flags
            return j_obj
        if isinstance(obj, IntValue):
            return obj.value
        if isinstance(obj, FloatValue):
            return obj.value
        if isinstance(obj, StringValue):
            if obj.is_newline:
                return "\n"
            else:
                return f"^{obj.value}"
        if isinstance(obj, ListValue):
            return Json.ink_list_to_j_object(obj)
        if isinstance(obj, DivertTargetValue):
            div_target_json_obj = {}
            div_target_json_obj["^->"] = obj.value.components_string
            return div_target_json_obj
        if isinstance(obj, VariablePointerValue):
            var_ptr_json_obj = {}
            var_ptr_json_obj["^var"] = obj.value
            var_ptr_json_obj["ci"] = obj.context_index
            return var_ptr_json_obj
        if isinstance(obj, Glue):
            return "<>"
        if isinstance(obj, ControlCommand):
            return Json._control_command_names[obj.command_type]
        if isinstance(obj, NativeFunctionCall):
            name = obj.name
            if name == "^":
                name = "L^"
            return name
        if isinstance(obj, VariableReference):
            j_obj = {}
            read_count_path = obj.path_string_for_count
            if read_count_path:
                j_obj["CNT?"] = read_count_path
            else:
                j_obj["VAR?"] = obj.name
            return j_obj
        if isinstance(obj, VariableAssignment):
            key = "VAR=" if obj.is_global else "temp="
            j_obj = {}
            j_obj[key] = obj.variable_name
            if not obj.is_new_declaration:
                j_obj["re"] = True
            return j_obj
        if isinstance(obj, Void):
            return "void"
        if isinstance(obj, Tag):
            j_obj = {}
            j_obj["#"] = obj.text
            return j_obj
        if isinstance(obj, Choice):
            return Json.choice_to_j_object(obj)
        raise Exception(f"Failed to convert runtime object to Json token: {obj}")

    @staticmethod
    def container_to_j_array(container: Container) -> List[Any]:
        j_array = Json.list_to_jarray(container.content)
        named_only_content = container.named_only_content
        count_flags = container.count_flags
        if named_only_content and len(named_only_content) > 0 or count_flags > 0 or container.name:
            if named_only_content:
                terminating_obj = Json.dictionary_runtime_objs_to_j_object(named_only_content)

                for key, value in terminating_obj.items():
                    if isinstance(value, list):
                        attr_j_obj = value[-1]
                        if isinstance(attr_j_obj, dict):
                            attr_j_obj.pop("#n")
                            if len(attr_j_obj) == 0:
                                value[-1] = None
            else:
                terminating_obj = {}
            if count_flags > 0:
                terminating_obj["#f"] = count_flags
            if container.name:
                terminating_obj["#n"] = container.name
            j_array.append(terminating_obj)
        else:
            j_array.append(None)
        return j_array

    @staticmethod
    def j_array_to_container(j_array: List[Any]) -> Container:
        container = Container()
        container.content = Json.j_array_to_runtime_obj_list(j_array, skip_last=True)

        terminating_obj = j_array[-1]
        if isinstance(terminating_obj, dict):
            named_only_content = {}
            for key, value in terminating_obj:
                if key == "#f":
                    container.count_flags = int(value)
                elif key == "#n":
                    container.name = str(value)
                else:
                    named_content_item = Json.j_token_to_runtime_object(value)
                    if isinstance(named_content_item, Container):
                        named_content_item.name = key
                    named_only_content[key] = named_content_item
            container.named_only_content = named_only_content
        return container

    @staticmethod
    def j_object_to_choice(j_obj: Dict[str, Any]) -> Choice:
        choice = Choice()
        choice.text = str(j_obj["text"])
        choice.index = int(j_obj["index"])
        choice.source_path = str(j_obj["original_choice_path"])
        choice.original_thread_index = int(j_obj["original_thread_index"])
        choice.path_string_on_choice = str(j_obj["target_path"])
        return choice

    @staticmethod
    def choice_to_j_object(choice: Choice) -> Dict[str, Any]:
        j_obj = {
            "text": choice.text,
            "index": choice.index,
            "original_choice_path": choice.source_path,
            "original_thread_index": choice.original_thread_index,
            "target_path": choice.path_string_on_choice
        }
        return j_obj

    @staticmethod
    def ink_list_to_j_object(list_val: ListValue) -> Dict[str, Any]:
        raw_list = list_val.value
        dictionary = {}
        content = {}
        for key, value in raw_list.items():
            content[str(key)] = value
        dictionary["list"] = content
        if len(raw_list) == 0 and raw_list.origin_names and len(raw_list.origin_names) > 0:
            dictionary["origins"] = raw_list.origin_names
        return dictionary

    @staticmethod
    def list_definitions_to_j_token(origin: ListDefinitionOrigin) -> Dict[str, Any]:
        result = {}
        for definition in origin.lists:
            list_def_json = {}
            for key, value in definition.items.items():
                list_def_json[key.item_name] = value
            result[definition.name] = list_def_json
        return result

    @staticmethod
    def j_token_to_list_definitions(obj: Dict[str, Any]) -> ListDefinitionOrigin:
        all_defs = []
        for key, value in obj.items():
            items = {}
            for k, v in value.items():
                items[k] = int(v)
            definition = ListDefinition(key, items)
            all_defs.append(definition)
        return ListDefinitionOrigin(all_defs)

    _control_command_names[CommandType.EvalStart] = "ev"
    _control_command_names[CommandType.EvalOutput] = "out"
    _control_command_names[CommandType.EvalEnd] = "/ev"
    _control_command_names[CommandType.Duplicate] = "du"
    _control_command_names[CommandType.PopEvaluatedValue] = "pop"
    _control_command_names[CommandType.PopFunction] = "~ret"
    _control_command_names[CommandType.PopTunnel] = "->->"
    _control_command_names[CommandType.BeginString] = "str"
    _control_command_names[CommandType.EndString] = "/str"
    _control_command_names[CommandType.NoOp] = "nop"
    _control_command_names[CommandType.ChoiceCount] = "choiceCnt"
    _control_command_names[CommandType.TurnsSince] = "turns"
    _control_command_names[CommandType.ReadCount] = "readc"
    _control_command_names[CommandType.Random] = "rnd"
    _control_command_names[CommandType.SeedRandom] = "srnd"
    _control_command_names[CommandType.VisitIndex] = "visit"
    _control_command_names[CommandType.SequenceShuffleIndex] = "seq"
    _control_command_names[CommandType.StartThread] = "thread"
    _control_command_names[CommandType.Done] = "done"
    _control_command_names[CommandType.End] = "end"
    _control_command_names[CommandType.ListFromInt] = "listInt"
    _control_command_names[CommandType.ListRange] = "range"

    for i in range(CommandType.TOTAL_VALUES):
        if not _control_command_names:
            raise Exception("Control command not accounted for in serialisation")
