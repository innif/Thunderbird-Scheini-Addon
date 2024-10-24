import email
import imaplib
from configparser import ConfigParser

#Read config.ini file
config_object = ConfigParser()
config_object.read("mail_analyzer/config.ini")
mail_config = config_object["MAIL"]


EMAIL = mail_config["email"]
PASSWORD = mail_config["password"]
SERVER = mail_config["server"]

mail = imaplib.IMAP4_SSL(SERVER)
mail.login(EMAIL, PASSWORD)
mail.select('inbox')
status, data = mail.search(None, 'ALL')
mail_ids = []
for block in data:
    mail_ids += block.split()

for i in mail_ids:
    status, data = mail.fetch(i, '(RFC822)')
    for response_part in data:
        if isinstance(response_part, tuple):
            message = email.message_from_bytes(response_part[1])
            mail_from = message['from']
            mail_subject = message['subject']
            print(message)
            if message.is_multipart():
                mail_content = ''

                for part in message.get_payload():
                    print(part.get_content_type())
                    if part.get_content_type() == 'text/plain':
                        mail_content += part.get_payload(decode=True).decode()
                    if part.get_content_type() == 'text/html':
                        mail_content += part.get_payload(decode=True).decode()
            else:
                print("message is not multipart")
                mail_content = message.get_payload()
            print(f'From: {mail_from}')
            print(f'Subject: {mail_subject}')
            print(f'Content: {mail_content}')