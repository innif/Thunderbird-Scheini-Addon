from openai import OpenAI
from configparser import ConfigParser
import datetime
import json
import requests

#Read config.ini file
config_object = ConfigParser()
config_object.read("mail_analyzer/config.ini")
openai_conf = config_object["OPENAI"]
server_conf = config_object["SERVER"]

prompt = open("mail_analyzer/prompt.txt", "r", encoding="utf-8").read()
date_promt = open("mail_analyzer/prompt_dates.txt", "r", encoding="utf-8").read()

client = OpenAI(api_key=openai_conf["api_key"])

def find_dates(mail_content):
    # add current date to prompt
    date_promt_copy = date_promt + datetime.datetime.now().strftime("%a %Y-%m-%d")

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": date_promt_copy},
            {"role": "user", "content": mail_content},
            {"role": "user", "content": "Finde die Daten in der Mail."}
        ]
    )
    return completion.choices[0].message.content

def analyze_mail(mail_content):
    date_resp = find_dates(mail_content)
    dates = json.loads(date_resp)["dates"]

    prompt_copy = prompt + "\n"
    

    for d in dates:
        event_details = requests.get(
            "{}/events/{}".format(server_conf["host"], d), 
            auth=(server_conf["user"], server_conf["password"])
        ).json()
        assert isinstance(event_details, dict)
        event_details.pop("technician", None)
        event_details.pop("num_artists", None)
        prompt_copy += json.dumps(event_details, indent=4) + "\n"
    prompt_copy += "\n\nHeute ist " + datetime.datetime.now().strftime("%a %Y-%m-%d")
    completion = client.chat.completions.create(
        model="gpt-4-turbo",	
        messages=[
            {"role": "system", "content": prompt_copy},
            {"role": "user", "content": mail_content},
            {"role": "user", "content": "Analysiere die Mail. Achte auf die maximale Anzahl an Sitzplätzen."}
        ]
    )

    text = completion.choices[0].message.content
 
    # # https://rotes-buch.scheinbar.de:5000/events/2024-10-24
    return json.loads(text)