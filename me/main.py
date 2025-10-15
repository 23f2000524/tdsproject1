# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi[standard]",
#   "uvicorn",
#   "requests"
# ]
# ///
import os
import requests
from fastapi import FastAPI
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 

def validate_secret(secret: str) -> bool:
    return secret == os.getenv("SECRET_KEY")

def round1(data):
    files = write_code_with_llm()
    
    create_repo(f"{data['id']}_{data['nonce']}")
    enable_pages(f"{data['id']}_{data['nonce']}")
    push_files_to_pages(f"{data['id']}_{data['nonce']}",files, 1)
import base64

def round1(data):
    prompt = f"""
    You are to create a simple web app based on this brief:
    {data['brief']}
    Make sure it works when deployed to GitHub Pages.
    Use HTML + JS + minimal CSS.
    """
    files = write_code_with_llm(prompt)
    
    repo_name = f"{data['id']}-{data['nonce']}"
    create_repo(repo_name)
    enable_pages(repo_name)
    
    # Encode files to base64 before pushing
    for f in files:
        f["content"] = base64.b64encode(f["content"].encode()).decode()

    push_files_to_pages(repo_name, files, 1)

    # Send POST back to evaluation URL
    post_evaluation(data, repo_name)


def round2():
    pass


def create_repo(name: str):
    payload={"name":name,
              "private": False,
              "auto_init": True,
              "lisence_template": "mit"}
    header={"Authorization": f"Bearer {GITHUB_TOKEN}",
                 "Accept": "application/vnd.github.v3+json"}
    response = requests.post(
        "https://api.github.com/user/repos",
        headers=header,
        json=payload
              )
    if response.status_code != 201:
        return Exception(f"Failed to create repo : {response.status_code}, {response.text}")
    else:
        return response.json()

def enable_pages(repo_name: str):
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
        }
    payload={
        "source":{
            "branch":"main",
            "path":"/"
            },
        "build_type":"legacy"}
    response = requests.post(
        f"https://api.github.com/repos/23f2000524/{repo_name}/pages",
        headers=headers,
        json=payload
              )
    if response.status_code != 201:
        return Exception(f"Failed to enable pages : {response.status_code}, {response.text}")
    else:     
        return response.json()
    

def get_sha_of_latest_commit(repo_name: str, branch: str="main") -> str:
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
        }
    response = requests.get(
        f"https://api.github.com/repos/23f2000524/{repo_name}/git/refs/heads/{branch}",
        headers=headers
              )
    if response.status_code != 200:
        return Exception(f"Failed to get file sha : {response.status_code}, {response.text}")
    else:
        return response.json()["object"]["sha"]
    

def push_files_to_pages(repo_name: str,files:list[dict],round:int):
    if round == 2:
        latest_sha = get_sha_of_latest_commit(repo_name)
    else:
        latest_sha = None

    for file in files:
        file_name=file.get("name")
        file_content=file.get("content")
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
            }
        payload={
            "message": f"Add {file_name}",
            "content": file_content
                }
        
        if not isinstance(file_content, bytes):
            file_content = file_content.encode("utf-8")
        b64_content = base64.b64encode(file_content).decode("utf-8")


        if latest_sha:
            payload["sha"] = latest_sha
        response = requests.put(
            f"https://api.github.com/repos/23f2000524/{repo_name}/contents/{file_name}",
            headers=headers,
            json=payload
                  )
        if response.status_code not in [201]:
            return Exception(f"Failed to push file {file_name} : {response.status_code}, {response.text}")
    return {"message": "All files pushed successfully"}

def write_code_with_llm(prompt: str):
    API_URL = "https://aipipe.org/openai/v1/chat/completions"
    API_KEY = os.getenv("AIAPI_KEY")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.7
    }

    resp = requests.post(API_URL, headers=headers, json=data)
    if resp.status_code != 200:
        raise Exception(f"LLM API error: {resp.text}")

    code = resp.json()["choices"][0]["message"]["content"]
    return [
        {"name": "index.html", "content": code.encode("utf-8").decode("utf-8")},
        {"name": "README.md", "content": f"# Generated App\n\n{prompt}\n\n---\n\n{code}"}
    ]

def post_evaluation(data, repo_name):
    payload = {
        "email": data["email"],
        "task": data["task"],
        "round": data["round"],
        "nonce": data["nonce"],
        "repo_url": f"https://github.com/23f2000524/{repo_name}",
        "commit_sha": "latest",  # optional: fetch via API
        "pages_url": f"https://23f2000524.github.io/{repo_name}/"
    }
    headers = {"Content-Type": "application/json"}
    r = requests.post(data["evaluation_url"], headers=headers, json=payload)
    if r.status_code != 200:
        raise Exception(f"Eval post failed: {r.status_code} - {r.text}")
    return True



app = FastAPI()

@app.post("/handle_task")
def handle_task(data: dict):
    if not validate_secret(data.get("secret", "")):
        return {"error": "Incorrect secret"}
    else:
        if data.get("round") == 1:
            round1(data)
            return {"message": "Round 1 started"}
        elif data.get("round") == 2:
            round2(data)
            return {"message": "Round 2 started"}
        else:
            return {"error", "Invalid round"}
    print(data)
    return {"message": "Task recieved", "data": data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)