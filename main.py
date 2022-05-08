import openai
import googletrans
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

dotenv.load_dotenv()

openai.api_key = os.getenv("API_KEY")
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")
translator = googletrans.Translator()

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent="<console:lonunm:1.0>",
    username="lonunm",
    password=os.getenv("PASSWORD")
)

def Translate(text, _from, to):
    return translator.translate(text, src=_from, dest=to).text

def UrlToImg(url, save_as=''):
    img = Image.open(BytesIO(requests.get(url).content))
    if save_as:
        img.save(save_as)
    return np.array(img)

def ResizeImg(img, max_height, max_width):
    height, width = img.shape[:2]

    if max_height < height or max_width < width:
        scaling_factor = max_height / float(height)
        if max_width/float(width) < scaling_factor:
            scaling_factor = max_width / float(width)
        img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
    return img

def ReadTexts(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    threshold_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(threshold_img, lang='tur')
    return text.strip()

def Send(text):
    text = Translate(text, "tr", "en")
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, funny and very friendly.\n\nHuman: {text}\nAI:",
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
    )
    
    response = response.choices[0].text.strip()
    return Translate(response, "en", "tr")

def ReplyAll():
    inbox = reddit.inbox.unread()

    for message in inbox:
        message.reply(Send(message.body))
        message.mark_read()

def CommentHotPosts(sbrddt, lmt=10):
    subreddit = reddit.subreddit(sbrddt)
    for post in subreddit.hot(limit=lmt):
        replied = False
        for comment in  post.comments:
            if comment.author == "lonunm":
                replied = True
                break

        if not replied:
            text = f"{post.title} {post.selftext}"
            if post.url.endswith(".jpg"):
                img = UrlToImg(post.url)
                img = ResizeImg(img, 400, 400)
                img_text = unidecode.unidecode(ReadTexts(img)).strip()
                text += img_text
            response = Send(text)
            post.reply(response)

ReplyAll()
CommentHotPosts("ZargoryanGalaksisi", 10)