from ai_analyze import analyze_mail, find_dates
import json

mail_content = open("mail_analyzer/mail.txt", "r", encoding="utf-8").read()

resp = analyze_mail(mail_content)
print(resp)
resp = json.loads(resp)

#print(resp)
print(resp.get("response_mail"))