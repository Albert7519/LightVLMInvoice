import re

def parse_amount(amt_str):
    if not amt_str: return 0.0
    digits = re.sub(r'[^\d\.]', '', str(amt_str))
    try: return float(digits) if digits else 0.0
    except: return 0.0

