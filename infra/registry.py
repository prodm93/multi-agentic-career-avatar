import os


LLM_CONFIG = {
    'gemini-3-flash-preview': {  
        'api_endpoint': 'https://generativelanguage.googleapis.com/v1beta/',
        'api_key': os.getenv('GEMINI_API_KEY'),
        'providers': ['Google'],
        'tier_plan': 'Free',
        'prefix': '',
        'get_base_name': lambda s: s.split('/')[-1],
        'handle_api_path': lambda s: s,
        'fallback_rpm': 5,
        'fallback_tpm': 250000
    },
    
    'llama-3.3-70b-versatile': {
        'api_endpoint': 'https://api.groq.com/openai/v1',
        'api_key': os.getenv('GROQ_API_KEY'),
        'providers': ['Groq'],
        'tier_plan': 'Free',
        'prefix': 'groq/',
        'get_base_name': lambda s: s.split('/')[-1],
        'handle_api_path': lambda s: f"groq/{s.removeprefix('groq/')}",
        'fallback_rpm': 30,
        'fallback_tpm': 8000

    },

    'openai/gpt-oss-120b': {
        'api_endpoint': 'https://api.groq.com/openai/v1',
        'api_key': os.getenv('GROQ_API_KEY'),
        'providers': ['Groq', 'OpenAI'],
        'tier_plan': 'Free',
        'prefix': 'groq/',
        'get_base_name': lambda s: s.split('/')[-1],
        'handle_api_path': lambda s: f"groq/{s.removeprefix('groq/')}",
        'fallback_rpm': 30,
        'fallback_tpm': 8000

    },

    'qwen/qwen3-32b': {
        'api_endpoint': 'https://api.groq.com/openai/v1',
        'api_key': os.getenv('GROQ_API_KEY'),
        'providers': ['Groq', 'Qwen'],
        'tier_plan': 'Free',
        'prefix': 'groq/',
        'get_base_name': lambda s: s.split('/')[-1],
        'handle_api_path': lambda s: f"groq/{s.removeprefix('groq/')}",
        'fallback_rpm': 30,
        'fallback_tpm': 8000
        
    },

    'unavailable_model': {
        'api_endpoint': None,
        'api_key': None,
        'providers': None,
        'tier_plan': None,
        'prefix': None,
        'get_base_name': lambda s: None,
        'handle_api_path': lambda s: None,
        'fallback_rpm': 0,
        'fallback_tpm': 0

    } 
}  

""" 'moonshotai/kimi-k2-instruct-0905': {
        'api_endpoint': 'https://api.groq.com/openai/v1',
        'api_key': os.getenv('GROQ_API_KEY'),
        'providers': ['Groq', 'Moonshot'],
        'tier_plan': 'Free',
        'prefix': 'groq/',
        'get_base_name': lambda s: s.split('/')[-1],
        'handle_api_path': lambda s: f"groq/{s.removeprefix('groq/')}",
        'fallback_rpm': 30,
        'fallback_tpm': 8000

    }, """ #deprecated from groq
