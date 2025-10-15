# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests"
# ]
# ///
import requests, os

# use this proxy https://aipipe.org/openai/v1 to send a request to open ai api with model gpt o4 mini
API_URL = "https://aipipe.org/openai/v1/chat/completions"
API_KEY = os.getenv("AIAPI_KEY")


def generate_code(prompt: str) -> str:    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    json_data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    response = requests.post(API_URL, headers=headers, json=json_data)    
    os.getenv("AIAPI_KEY")
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
    

if __name__ == "__main__":
    prompt = "Write a python function that adds two numbers, your output should be only the code block without any explanation or markdown formatting. The function should be named add_numbers and take two parameters num1 and num2. it should be directly runnable code, should not include any backticks or anything, add comments about usage of functions."
    with open("generated_code.py", "w") as f:
        f.write(generate_code(prompt))