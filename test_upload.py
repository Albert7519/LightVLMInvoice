import requests
import time
import sys
import json

API_BASE = 'http://localhost:8080/api/v1/invoices'
FILE_PATH = sys.argv[1] if len(sys.argv) > 1 else '/home/albert/CodeProjects/LocalllmOcrMK2/testFiles/日本发票2.pdf'

print(f"Uploading {FILE_PATH}...")
with open(FILE_PATH, 'rb') as f:
    res = requests.post(f"{API_BASE}/extract", files={'files': f})

task_id = res.json()['data']['task_ids'][0]

while True:
    st = requests.get(f"{API_BASE}/status/{task_id}")
    data = st.json()
    if data['status'] in ('COMPLETED', 'FAILED'):
        invoices = data.get('result', {}).get('invoices', [])
        print(f"\nFinal extracted invoices: {len(invoices)}\n")
        print("Invoice numbers found:")
        for idx, inv in enumerate(invoices):
            print(f"{idx+1}: {inv.get('invoice_number')}")
        break
    time.sleep(2)
