import openai
import googletrans
import praw
import os
import dotenv

dotenv.load_dotenv()

openai.api_key = os.getenv("API_KEY")
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

def Send(text):
    text = Translate(text, "tr", "en")
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Human: {text}\n AI:",
        temperature=1,
        max_tokens=150,
        top_p=1,
        frequency_penalty=1,
        presence_penalty=1,
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
            response = Send(text)
            post.reply(response)

CommentHotPosts("Test2750")
ReplyAll()