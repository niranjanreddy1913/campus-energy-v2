"""Part 1 — call the RUNNING calculator API over HTTP, the way a browser or another program would, and print every reply.
Start the API first:   python 1_calculator_api.py          (port 8000)
Then, in a second terminal:   python 2_test_calculator.py
API on another port?   API_URL=http://127.0.0.1:8010 python 2_test_calculator.py"""
import os
import sys

import httpx

API = os.environ.get("API_URL", "http://127.0.0.1:8000")         # where 1_calculator_api.py runs
client = httpx.Client(base_url=API, timeout=10)

try:                                                              # first ask WHO is on that port: it must be the Calculator API
    who = client.get("/").json().get("message", "")
except httpx.ConnectError:
    sys.exit(f"✗ Nothing is running at {API}. Start the API first:  python 1_calculator_api.py")
if "Calculator API" not in who:
    sys.exit(f"✗ The program at {API} is not the Calculator API ({who}). Start it:  python 1_calculator_api.py")
print(f"Testing the Calculator API at {API}\n")


def show(method, url, body=None):
    r = client.request(method, url, json=body)
    reply = r.json()
    if r.status_code == 422:                          # FastAPI explains every broken rule; show the first one, and where
        e = reply["detail"][0]
        reply = f"{e['msg']}  (in {e['loc'][0]}: {e['loc'][-1]})"
    print(f"{method:<5} {url:<32} {str(body or ''):<32} → {r.status_code} {reply}")


print("GET — inputs in the address:")
show("GET", "/calculate?a=12&b=3&op=div")         # 200: the answer
show("GET", "/calculate?a=7&b=6&op=mul")
show("GET", "/calculate?a=1&b=0&op=div")          # 400: our function refused the values
show("GET", "/calculate?a=2&b=3&op=pow")          # 422: the request broke the rules — our code never ran
show("GET", "/calculate?a=twelve&b=3&op=add")     # 422: a is not a number

print("\nPOST — the same calculation, inputs in a JSON body:")
show("POST", "/calculate", {"a": 12, "b": 3, "op": "div"})
show("POST", "/calculate", {"a": 1, "b": 0, "op": "div"})
show("POST", "/calculate", {"a": 12, "op": "add"})  # 422: b is missing
