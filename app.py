# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi[standard]",
#   "uvicorn",
#   "requests",
# ]
# ///
import os
import requests
import base64
from fastapi import FastAPI
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 

def validate_secret(secret: str) -> bool:
    return secret == os.getenv("SECRET_KEY")



def round1(data):
    if data.get("attachments", []):
        attachfiles = parse_attachments(data)
    if data.get("checks", []):
        checks = data["checks"]

    if attachfiles:
        attach_text = "\n\n".join([f"{f['name']}\n{f['content']}" for f in attachfiles])
    else:
        attach_text = "No attachments provided"

    if checks:
        checks_text = "\n".join(checks)
    else:
        checks_text = "No checks provided"
    prompt = f"""
    You are to create a simple web app based on this brief:
    {data['brief']}
    Make sure it works when deployed to GitHub Pages.
    Use HTML + JS + minimal CSS.
    include only code files and no explanations or markdown formatting.
    The app should be contained in a single HTML file named index.html.
    The following are the attachments provided, you can use them as needed:
    {attach_text}    -------------
    it must pass the following checks:
    {checks_text}

    """

    files = write_code_with_llm(prompt)
    
    repo_name = f"{data['task']}-{data['nonce']}"
    create_repo(repo_name)
    enable_pages(repo_name)
    
    # Encode files to base64 before pushing

    commit_sha = push_files_to_pages(repo_name, files, 1)

    # Send POST back to evaluation URL
    post_evaluation(data, repo_name, commit_sha)

def parse_attachments(data: dict)-> list[dict]:
    """
    Parse attachments array and decode data: URIs into file objects:
    returns list of {"name": ..., "content": "..."}
    """
    def safe_b64decode(b64_str: str):
        # Strip whitespace/newlines
        b64_str = b64_str.strip()
        # Add padding if missing
        missing_padding = len(b64_str) % 4
        if missing_padding:
            b64_str += "=" * (4 - missing_padding)
        return base64.b64decode(b64_str)
    
    files = []
    for att in data.get("attachments", []):
        name = att.get("name")
        url = att.get("url", "")
        if not name or not url:
            continue
        if url.startswith("data:"):
            try:
                header, b64 = url.split(",", 1)
                decoded = safe_b64decode(b64)
                try:
                    text = decoded.decode("utf-8")
                    files.append({"name": name, "content": text, "binary": False})
                except UnicodeDecodeError:
                    b64_text = base64.b64encode(decoded).decode("utf-8")
                    files.append({"name": name, "content": b64_text, "binary": True})
            except Exception as e:
                raise ValueError(f"Invalid data URI for attachment {name}: {e}")
        else:
            # non-data URIs are not fetched for security/simplicity; treat as placeholder
            raise ValueError("Only data: attachments are supported by this service.")
    return files

def round2(data):

    repo_name = f"{data['task']}-{data['nonce']}"
    
    for i, subround in enumerate(data.get("round2", []), start=1):
        print(f"--- Starting Round 2.{i} ---")

        if subround.get("attachments", []):
            attachfiles = parse_attachments(subround)
        else:
            attachfiles = []

        checks = subround.get("checks", [])

        attach_text = "\n\n".join([f"{f['name']}\n{f['content']}" for f in attachfiles]) if attachfiles else "No new attachments provided"
        checks_text = "\n".join(checks) if checks else "No checks provided"

        prompt = f"""
        You are to modify the existing web app (index.html) based on this new brief:
        {subround['brief']}

        The app already exists in the GitHub repository: {repo_name}
        You must update the existing index.html to fulfill the new requirements.

        Keep using HTML + JS + minimal CSS.
        Maintain compatibility with GitHub Pages.

        Attachments (if any) that you can use:
        {attach_text}

        It must pass the following checks:
        {checks_text}

        Include only code (no markdown or explanation).
        The updated app must remain inside a single file: index.html.
        """

        # Generate the updated HTML with LLM
        files = write_code_with_llm(prompt)

        # Encode files to base64 before pushing

        # Push changes to GitHub (Round 2 update mode)
        commit_sha = push_files_to_pages(repo_name, files, 2)

        # Post evaluation for this sub-round
        post_evaluation(data, repo_name, commit_sha)

        print(f"✅ Completed Round 2.{i} | Commit SHA: {commit_sha}")
    




def create_repo(name: str):
    payload={"name":name,
              "private": False,
              "auto_init": False,
              "license_template": "mit"}
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
    
def get_file_sha(repo_name: str, file_path: str, branch: str = "main") -> str:
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(
        f"https://api.github.com/repos/23f2000524/{repo_name}/contents/{file_path}?ref={branch}",
        headers=headers
    )
    if resp.status_code != 200:
        raise Exception(f"Failed to get file sha for {file_path} : {resp.status_code}, {resp.text}")
    return resp.json()["sha"]


def push_files_to_pages(repo_name: str,files:list[dict],round:int):
    if round == 2:
        latest_sha = get_sha_of_latest_commit(repo_name)
    else:
        latest_sha = None

    commit_sha = None
    for file in files:
        file_name=file.get("name")
        file_content=file.get("content")
        binary=file.get("binary", False)
        if not isinstance(file_content, bytes):
            if binary:
                # base64 string -> bytes
                file_content = base64.b64decode(file_content)
            else:
                file_content = file_content.encode("utf-8")
        b64_content = base64.b64encode(file_content).decode("utf-8")
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
            }
        payload={
            "message": f"Update {file_name}" if latest_sha else f"Add {file_name}",
            "content": b64_content
                }
        

        sha = get_file_sha(repo_name, file_name) if round == 2 else None
        if sha :
            payload["sha"] = sha
        response = requests.put(
            f"https://api.github.com/repos/23f2000524/{repo_name}/contents/{file_name}",
            headers=headers,
            json=payload
                  )
        if response.status_code not in [200,201]:
            raise Exception(f"Failed to push file {file_name} : {response.status_code}, {response.text}")
        commit_sha = response.json()["commit"]["sha"]
    return commit_sha

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
        raise Exception(f"LLM API error: {resp.status_code} - {resp.text}")

    code = resp.json()["choices"][0]["message"]["content"].strip()
    return [
        {"name": "index.html", "content": code},
        {"name": "README.md", "content": f"# Generated App\n\n## Latest Code Generated based on :\n{prompt}\n\n---\n\n## Generated Code\n\n{code}"}    ]

def post_evaluation(data, repo_name, commit_sha):
    payload = {
        "email": data["email"],
        "task": data["task"],
        "round": data["round"],
        "nonce": data["nonce"],
        "repo_url": f"https://github.com/23f2000524/{repo_name}",
        "commit_sha": commit_sha,  # optional: fetch via API
        "pages_url": f"https://23f2000524.github.io/{repo_name}/"
    }
    print(payload)
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
            return {"error": "Invalid round"}
    print(data)
    return {"message": "Task recieved", "data": data}


@app.get("/")
def root():
    return {"message": "API is running. Use /handle_task for POST requests."}
