from app.config import settings 
import requests
import json

def ask_perplexity(system_instructions, user_message):
    url = "https://api.perplexity.ai/chat/completions"
    api_key = settings.PERPLEXITY_API_KEY
    payload = {
        "model": "sonar-pro", 
        "messages": [
            {
                "role": "system",
                "content": system_instructions
            },
            {
                "role": "user", 
                "content": user_message
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": None,
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "response_format": None
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    response_json = json.loads(response.text)
    
    message_content = response_json["choices"][0]["message"]["content"]
    citations = response_json["citations"]
    
    return message_content, citations
