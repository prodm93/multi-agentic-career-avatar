import types
from tools.functions import (
    record_user_details,
    record_unknown_question,
    search_company,
    search_role_requirements
)

from tools.definitions import (
    record_user_details_json,
    record_unknown_question_json,
    search_company_json,
    search_role_requirements_json
)


_tool_fn_dict = { 
        tool_name: tool_fn for tool_name, tool_fn in globals().items() 
                 if isinstance(tool_fn, types.FunctionType) and 
                 hasattr(tool_fn, '__module__') and 
                 tool_fn.__module__=='tools.functions'
            }

_tool_def_dict = {
        tool_def_name.removesuffix('_json'): tool_def for tool_def_name, tool_def in globals().items() 
                if isinstance(tool_def, dict) and
                list(tool_def.keys()) == ['name', 'description', 'parameters']
    }

TOOL_REGISTRY = {
        tool_name: {
                'tool_fn': _tool_fn_dict[tool_name], 
                'tool_def': _tool_def_dict[tool_name]
                } for tool_name in _tool_fn_dict.keys()
            }


