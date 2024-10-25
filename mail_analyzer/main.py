import email
import email.parser
import imaplib
import smtplib
from configparser import ConfigParser
import time
from ai_analyze import analyze_mail

#Read config.ini file
config_object = ConfigParser()
config_object.read("mail_analyzer/config.ini")
mail_config = config_object["MAIL"]

EMAIL = mail_config["email"]
PASSWORD = mail_config["password"]
SERVER_IMAP = mail_config["server_imap"]
SERVER_SMTP = mail_config["server_smtp"]

mail_imap = imaplib.IMAP4_SSL(SERVER_IMAP)
mail_imap.login(EMAIL, PASSWORD)
mail_imap.select('inbox')

mail_smtp = smtplib.SMTP_SSL(SERVER_SMTP)
mail_smtp.login(EMAIL, PASSWORD)

def fetch_mails():
    # return oldest unread mail
    result, data = mail_imap.search(None, 'UNSEEN')
    mail_ids = data[0]
    id_list = mail_ids.split()
    if not id_list:
        return None
    first_email_id = int(id_list[0])
    result, data = mail_imap.fetch(str(first_email_id), '(RFC822)')
    mail_imap.store(str(first_email_id),'+FLAGS','\Seen')
    for response_part in data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            return msg

def decode_mail(msg):
    out = ""
    out += "From: {}\n".format(msg["from"])
    out += "Subject: {}\n".format(msg["subject"])
    out += "Date: {}\n\n".format(msg["date"])
    for part in msg.walk():
        if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
            out += part.get_payload(decode=True).decode("utf-8")
    return out

def respond_mail(msg, output):
    text = ""
    reservations = output["bookings"]
    for r in reservations:
        date = r["date"]
        name = r["name"]
        quantity = r["quantity"]
        comment = r["comment"]
        text += "Datum: {}<br>Name: {}<br>Anzahl: {}<br>Kommentar: {}<br>".format(date, name, quantity, comment)
            # "date": "YYYY-MM-DD",
            # "name": "Max Mustermann",
            # "quantity": 3,
            # "comment": "kommen etwas später"
        link = "http://localhost:8001/event/{}/add?name={}&quantity={}&comment={}".format(date, name, quantity, comment)
        #include link as html
        text += "<a href='{}'>Reservierung hinzufügen</a>".format(link)
    text += "<br><hr>"
    text += output["response_mail"].replace("\n", "<br>")
    msg_out = email.message.EmailMessage()
    msg_out["from"] = EMAIL
    msg_out["to"] = msg["from"]
    msg_out["subject"] = "Re: " + msg["subject"]
    msg_out.set_content(text, subtype="html")

    mail_smtp.sendmail(EMAIL, msg["from"], msg_out.as_string())

while True:
    print("fetching mails")
    msg = fetch_mails()
    if not msg:
        time.sleep(5)
        continue
    msg_text = decode_mail(msg)
    output = analyze_mail(msg_text)
    respond_mail(msg, output)

    print(msg_text)