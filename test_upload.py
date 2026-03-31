import requests
import time
import sys

API_BASE = 'http://localhost:8080/api/v1/invoices'
FILE_PATH = '/home/albert/CodeProjects/LocalllmOcrMK2/testFiles/SKM.pdf'

print(f"Uploading {FILE_PATH}...")
with open(FILE_PATH, 'rb') as f:
    res = requests.post(f"{API_BASE}/extract", files={'files': f})

print("Upload response:", res.status_code, res.text)
if res.status_code != 200:
    sys.exit(1)

task_id = res.json()['data']['task_ids'][0]
print("Task ID:", task_id)

while True:
    st = requests.get(f"{API_BASE}/status/{task_id}")
    data = st.json()
    print("Status:", data['status'], "Progress:", data.get('progress'), data.get('message'))
    if data['status'] in ('COMPLETED', 'FAILED'):
        print(data)
        break
    time.sleep(2)
