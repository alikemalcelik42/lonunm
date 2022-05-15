import openai
import googletrans
from pandas import datetime
import praw
import os
import dotenv
import requests
import numpy as np
from io import BytesIO
from PIL import Image
import cv2
import pytesseract
import unidecode
import time
import datetime

dotenv.load_dotenv()

openai.api_key = os.getenv("API_KEY")
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")
translator = googletrans.Translator()

log_file_path = os.getenv("LOG_FILE_PATH")
definition = os.getenv("DEFINITION")
subreddit_name = os.getenv("SUBREDDIT_NAME")
limit = int(os.getenv("LIMIT"))
countdown = int(os.getenv("COUNTDOWN"))

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=f"<console:lonunm:1.0>",
    username="lonunm",
    password=os.getenv("PASSWORD")
)

def Log(request, response, author, subreddit):
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(f"Request: '{request}'\nResponse: '{response}'\nAuthor: '{author}'\nSubreddit: '{subreddit}'\nDate: {datetime.datetime.now()}\n\n")

def LogError(error, request, author, subreddit):
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(f"Error: {error}¨\nRequest: '{request}'\nAuthor: '{author}'\nSubreddit: '{subreddit}'\nDate: {datetime.datetime.now()}\n\n")

def Translate(text, _from, to):
    return translator.translate(text, src=_from, dest=to).text

def ConvertUrlToImg(url):
    img = Image.open(BytesIO(requests.get(url).content))
    return np.array(img)

def ResizeImg(img, max_height, max_width):
    height, width = img.shape[:2]

    if max_height < height or max_width < width:
        scaling_factor = max_height / float(height)
        if max_width/float(width) < scaling_factor:
            scaling_factor = max_width / float(width)
        img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
    return img

def ReadTextFromImg(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    threshold_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(threshold_img, lang='tur')
    text = unidecode.unidecode(text).strip()
    return text

def SendAI(request):
    request = Translate(request, "tr", "en")
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"{definition}\n\nHuman: {request}\nAI:",
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
    )
    
    response = response.choices[0].text.strip()
    return Translate(response, "en", "tr")

def ReplyAllMessages():
    inbox = reddit.inbox.unread()

    for message in inbox:
        try:
            response = SendAI(message.body)
            message.reply(response)
            message.mark_read()
            Log(message.body, response, message.author, message.subreddit.display_name)
        except Exception as e:
            message.mark_read()
            LogError(e, message.body, message.author, message.subreddit.display_name)

def CommentHotPosts():
    subreddit = reddit.subreddit(subreddit_name)
    for post in subreddit.hot(limit=limit):
        replied = False
        for comment in  post.comments:
            if comment.author == "lonunm":
                replied = True
                break

        if not replied:
            request = f"{post.title} {post.selftext}"
            if post.url.endswith(".jpg"):
                img = ConvertUrlToImg(post.url)
                img = ResizeImg(img, 400, 400)
                img_text = ReadTextFromImg(img)
                request += img_text
            response = SendAI(request)
            
            try:
                post.reply(response)
                Log(request, response, post.author, post.subreddit.display_name)
            except Exception as e:
                LogError(e, request, post.author, post.subreddit.display_name)

while True:
    time.sleep(countdown)
    ReplyAllMessages()
    CommentHotPosts()