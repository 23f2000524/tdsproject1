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

def send_task():
    payload={
        "email": "student@example.com",
        "secret": os.getenv("SECRET_KEY"),
        "task": "captcha-solver-...",
        "round": 2,
        "nonce": "ab12-...",
        "brief": "Create a captcha solver that handles ?url=https://.../image.png. Default to attached sample.",
        "round2": [
            {
            "brief": "Show an aria-live alert #github-status that reports when a lookup starts, succeeds, or fails.",
            "checks": [
                "document.querySelector('#github-status').getAttribute('aria-live') === 'polite'",
                "!!document.querySelector('script').textContent.includes('github-status')"
            ]
            },
            {
            "brief": "Display the account age in whole years inside #github-account-age alongside the creation date.",
            "checks": [
                "parseInt(document.querySelector('#github-account-age').textContent, 10) >= 0",
                "document.querySelector('#github-account-age').textContent.toLowerCase().includes('years')"
            ]
            },
            {
            "brief": "Cache the last successful lookup in localStorage under 'github-user-${seed}' and repopulate the form on load.",
            "checks": [
                "!!document.querySelector('script').textContent.includes('localStorage.setItem(\"github-user-${seed}\")')",
                "!!document.querySelector('script').textContent.includes('localStorage.getItem(\"github-user-${seed}\")')"
            ]
            }
        ],
        "evaluation_url": "https://example.com/notify",
        }
    response = requests.post("http://localhost:8000/handle_task", json=payload)
    print(response.json() )

if __name__ == "__main__":
    send_task()