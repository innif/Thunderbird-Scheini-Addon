import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import json
from ai_analyze import analyze_mail

app = fastapi.FastAPI()

origins = [
    "http://localhost:*",
    "http://127.0.0.1:*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# {
#     subject: messageHeader.subject,
#     author: messageHeader.author,
#     body: messageHeader.body,
# }

def display_html(output):
    text = ""
    reservations = output["bookings"]
    for r in reservations:
        date = r["date"]
        name = r["name"]
        quantity = r["quantity"]
        comment = r["comment"]
        text += "Datum: {}<br>Name: {}<br>Anzahl: {}<br>Kommentar: {}<br>".format(date, name, quantity, comment)
        link = "http://localhost:8001/event/{}/add?name={}&quantity={}&comment={}".format(date, name, quantity, comment)
        #include link as html
        text += "<a href='{}'>Reservierung hinzufügen</a>".format(link)
    return text

def combine_parts(msg):
    out = ""
    if "body" in msg:
        content_type = msg.get("contentType", "")
        body_content = msg.get("body", "").replace("=\n", "")  # Entfernt quoted-printable breaks

        # Teil als HTML rendern, wenn es sich um HTML handelt, andernfalls als Text
        if content_type == "text/html":
            out += body_content
        elif content_type == "text/plain":
            out += body_content

        return msg["body"]
    if "parts" in msg:
        for part in msg["parts"]:
            out += combine_parts(part)
    return out

@app.post("/analyze")
async def analyze(request: Request):
    # get json body
    msg = await request.json()
    parts = msg.get("content", {})
    msg_string = combine_parts(parts)
    if len(msg_string) > 10000:
        return {"text": "Message too long"}
    res = analyze_mail(msg_string)
    text = display_html(res)
    # return as json
    return {"text": text}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)