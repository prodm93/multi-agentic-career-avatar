

""" Tool to record user details """
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "company_name": {
                "type": "string",
                "description": "The name of the company that the user is working for"
            },
            "company_role": {
                "type": "string",
                "description": "The role that the user holds at the company"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

""" Tool to record unknown questions """
record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

search_company_json = {
    "name": "search_web",
    "description": "Use this tool to search for information about a company, with a particular focus on the company size, the company's tools and platforms, their tech stack, the pain points they're solving, unmet needs and future scope, their team, and their workplace culture",

    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "The name of the company to search for"
            },
            "explored_roles": {
                "type": "array",
                "description": "The roles being explored for this company",
                "items": {
                    "type": "string"
                }
            },
            "industries_or_domains": {
                "type": "array",
                "description": "The industries or domains that the company operates in",
                "items": {
                    "type": "string"
                }   
            },
            "company_location": {
                "type": "string",
                "description": "The location of the company, as determined by the country or region"
            },
        },
        "required": ["company_name"],
        "additionalProperties": False
    }

}

search_role_requirements_json = {
    "name": "search_role_requirements",
    "description": "Use this tool to search for information about the requirements for a particular role being explored at the company being researched",
    "parameters": {
        "type": "object",
        "properties": {
            "explored_roles": {
                "type": "array",
                "description": "The roles to search for",
                "items": {
                    "type": "string"
                }   
            },
            "company_name": {
                "type": "string",
                "description": "The name of the company the role is being explored at"
            },
            "industries_or_domains": {
                "type": "array",
                "description": "The industries or domains that the company operates in",
                "items": {
                    "type": "string"
                }   
            },
        },
        "required": ["roles"],
        "additionalProperties": False
    }
}