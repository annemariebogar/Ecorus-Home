from flask import Flask, request, jsonify
import datetime
import requests
import re
from collections import Counter

app = Flask(__name__)

def get_top_stories(num):
    response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json').json()[:num]
    return response

def get_comment_list(sID):
    comments = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{sID}.json').json()
    if 'kids' in comments.keys():
        return comments['kids']
    return []

def get_comment(cID, punctuation=True):
    comment_text = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{cID}.json').json()['text']
    comment_text = re.sub(r'&quot;', ' ', comment_text)
    comment_text = re.sub(r'<p>', ' ', comment_text)
    comment_text = re.sub(r'&#x27;', '\'', comment_text)
    if not punctuation:
        comment_text = re.sub(r'[^\w\s]', '', comment_text)
    return comment_text

def get_agg_comment_list(storyLim, commentLim):
    comment_ids = []
    stories = get_top_stories(storyLim)
    for s in stories:
        if len(comment_ids) >= commentLim:
            break
        comment_ids += get_comment_list(int(s))
    return comment_ids

@app.route("/50comments", methods=['GET'])
def get_50_comments():
    comment_ids = get_agg_comment_list(100, 50)
    comments = [get_comment(c) for i,c in enumerate(comment_ids) if i<50]
    return jsonify(comments)

@app.route("/10mostusedwords", methods=['GET'])
def get_10_most_used_words():
    comments = []
    count = 0
    comment_ids = get_agg_comment_list(30, 100)
    for c in comment_ids:
        if count >=100:
            break
        comments += get_comment(c, True).split()
        count += 1
    c = Counter(comments).most_common(10)
    return jsonify([word[0] for word in c])

#@app.route("/mostusedwords", methods=['GET'])

if __name__=='__main__':
    app.run()