from agents import Tool
from tools.call_handlers import sdk_tool_call_handler
from tools.registry import TOOL_REGISTRY


handrolled_toolkit = {tool_name:
                    Tool(
                        name=tool_data['tool_def']['name'],
                        description=tool_data['tool_def']['description'],
                        params_json_schema=tool_data['tool_def']['parameters'],
                        on_invoke_tool=sdk_tool_call_handler 
                    ) for tool_name, tool_data in TOOL_REGISTRY.items()
                }

