import requests

headers = {"Rasuri keerthana": "r.keer2005@gmail.com"}  # put your real name and email

r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
print("STATUS:", r.status_code)
print("CONTENT-TYPE:", r.headers.get("content-type"))
print("BODY START:", r.text[:300])