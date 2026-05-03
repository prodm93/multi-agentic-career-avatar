import json
from agents import ToolContext
from tools.registry import TOOL_REGISTRY

""" Class wrapper for handrolled no-framework agentic workflow to handle tool calls made by LLM agents """
class ToolCallHandler:

    async def handle_tool_call(self, tool_calls):
        """ Method to handle tool calls iteratively """
        results = []
        for tool_call in tool_calls:
            tool_fn = TOOL_REGISTRY.get(tool_call.function.name, {}).get('tool_fn')
            arguments = json.loads(tool_call.function.arguments)
            result = await tool_fn(**arguments) if tool_fn else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    

async def sdk_tool_call_handler(ctx: ToolContext, args_json: str) -> str:
    args = json.loads(args_json)
    tool_fn = TOOL_REGISTRY.get(ctx.tool_name, {}).get('tool_fn')
    result = await tool_fn(**args)
    return result
    
    
        
