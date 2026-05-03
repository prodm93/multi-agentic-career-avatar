import uuid
import redis
import asyncio
import gradio as gr
from infra.lazy_init import kickstart_model_research, received_user_role_info
from persona_docs.vectordb_builder import check_and_build_vectordb
from agents import SQLiteSession

def get_user_id_state(user_id_state):
    if not user_id_state:
        user_id_state = str(uuid.uuid4())
    return user_id_state

#TODO
def user_message(message, history): #PLACEHOLDER
    # refine below later--mostly boilerplate placeholder code 
    return "", history + [[message, None]]

#TODO
async def bot_response_pipeline(gradio_history, user_id_state):
    session = SQLiteSession(f'career_avatar_conv_{user_id_state}')
    if len([message for message in session if message['role'] == 'user']) == 1: # flag for first user meaaage receipt
        async with asyncio.TaskGroup() as tg: # TaskGroup needs Python 3.11+
            task1 = tg.create_task(check_and_build_vectordb())
            task2 = tg.create_task(kickstart_model_research())
        persona_docs_index = await task1
        await task2
        # opportunity researcher runs here
        # followed right away by tone tailor agent
        # orchestrator runs here
    """more code here later"""
    
#TODO
async def main():
    with gr.Blocks() as ui:
        user_id_state = gr.BrowserState()
        ui.load(fn=get_user_id_state, inputs=[user_id_state], outputs=[user_id_state])
        session = SQLiteSession(f'career_avatar_conv_{user_id_state}')

        # refine below later--mostly boilerplate placeholder code 
        chatbot = gr.Chatbot()
        msg = gr.Textbox()
        msg.submit(bot_response_pipeline, [msg, chatbot], [msg, chatbot])

        """more code here later"""
    
    ui.launch()

if __name__ == '__main__':
    asyncio.run(main())