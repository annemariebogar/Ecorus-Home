from flask import Flask, jsonify
import re
from collections import Counter
import asyncio
import aiohttp
import threading
from bs4 import BeautifulSoup

app = Flask(__name__)

def clean_text(comment_text, punctuation=True):
    soup = BeautifulSoup(comment_text, "html.parser")
    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()
    text = ' '.join(soup.stripped_strings)
    text = re.sub(u'[,\u2019\u2122\u201c\u201d\u2026]', '', text)
    return text
    if not punctuation:
        comment_text = re.sub(r'[^\w\s]', '', comment_text)
    return text

async def access_HackerNews(session, url):
    async with session.get(url) as response:
        return await response.json()

async def get_top_stories(session, num):
    url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
    top_stories = await access_HackerNews(session, url)
    return top_stories[:num]

async def get_comment_list(session, sID):
    story = await access_HackerNews(session, f'https://hacker-news.firebaseio.com/v0/item/{sID}.json')
    return story.get('kids', [])

async def get_comment(session, cID, punctuation=True):
    comment = await access_HackerNews(session, f'https://hacker-news.firebaseio.com/v0/item/{cID}.json')
    comment_text = clean_text(comment.get('text', ''), punctuation)
    return comment_text

async def get_agg_comment_list(session, storyLim, commentLim=0):
    comment_ids = []
    stories = await get_top_stories(session, storyLim)
    for s in stories:
        if commentLim > 0 and len(comment_ids) >= commentLim:
            break
        comment_ids += await get_comment_list(session, int(s))
    return comment_ids

async def recurse_comment_list(session, cID):
    comments = []
    comment = await access_HackerNews(session, f'https://hacker-news.firebaseio.com/v0/item/{cID}.json')
    if 'kids' in comment:
        results = await asyncio.gather(*[recurse_comment_list(session, k) for k in comment['kids']])
        for result in results:
            comments += result
    if 'text' in comment:
        comment_text = clean_text(comment['text'], punctuation=False)
        comments += comment_text.split()
    return comments

async def get_most_common_words(session, comment_ids, commentLim, wordLim):
    comments = []
    count = 0
    for c in comment_ids:
        if count >= commentLim:
            break
        comment_text = await get_comment(session, c, False)
        comments += comment_text.split()
        count += 1
    c = Counter(comments).most_common(wordLim)
    return c

@app.route("/50comments", methods=['GET'])
async def get_50_comments():
    async with aiohttp.ClientSession() as session:
        comment_ids = await get_agg_comment_list(session, 100, 50)
        comments = [await get_comment(session, c) for i,c in enumerate(comment_ids) if i<50]
    return jsonify(comments)

@app.route("/10mostusedwords", methods=['GET'])
async def get_10_most_used_words():
    async with aiohttp.ClientSession() as session:
        comment_ids = await get_agg_comment_list(session, 30, 100)
        c = await get_most_common_words(session, comment_ids, 100, 10)
    return jsonify([word[0] for word in c])

@app.route("/mostusedwords", methods=['GET'])
async def get_most_used_words_all_comments():
    async with aiohttp.ClientSession() as session:
        comment_ids = await get_agg_comment_list(session, 10)
        comments = []
        for c in comment_ids:
            comments += await recurse_comment_list(session, c)
        c = Counter(comments).most_common(25)
    return jsonify([word[0] for word in c])

if __name__=='__main__':
    app.run(threaded = True)
