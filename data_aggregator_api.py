from flask import Flask, request, jsonify
import datetime
import requests
import re
from collections import Counter

app = Flask(__name__)

def clean_text(comment_text, punctuation=True):
    comment_text = comment_text.replace("&quot;", " ").replace("<p>", " ").replace("&#x27;", " ")
    if not punctuation:
        comment_text = re.sub(r'[^\w\s]', '', comment_text)
    return comment_text

def get_top_stories(num):
    response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json').json()[:num]
    return response

def get_comment_list(sID):
    story = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{sID}.json').json()
    #if 'kids' in story.keys():
    #    return story['kids']
    #return []
    return story.get('kids', [])

def get_comment(cID, punctuation=True):
    comment = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{cID}.json').json()
    comment_text = clean_text(comment.get('text', ''), punctuation)
    return comment_text

def get_agg_comment_list(storyLim, commentLim=0):
    comment_ids = []
    stories = get_top_stories(storyLim)
    for s in stories:
        if commentLim > 0 and len(comment_ids) >= commentLim:
            break
        comment_ids += get_comment_list(int(s))
    return comment_ids

def recurse_comment_list(cID):
    comments = []
    comment = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{cID}.json').json()
    if 'kids' in comment.keys():
        for k in comment['kids']:
            comments += recurse_comment_list(k)
    if 'text' in comment.keys():
        comment_text = clean_text(comment['text'], False)
        comments += comment_text.split()
    return comments

def get_most_common_words(comment_ids, commentLim, wordLim):
    comments = []
    count = 0
    for c in comment_ids:
        if count >=commentLim:
            break
        comments += get_comment(c, False).split()
        count += 1
    c = Counter(comments).most_common(wordLim)
    return c

@app.route("/50comments", methods=['GET'])
def get_50_comments():
    comment_ids = get_agg_comment_list(100, 50)
    comments = [get_comment(c) for i,c in enumerate(comment_ids) if i<50]
    return jsonify(comments)

@app.route("/10mostusedwords", methods=['GET'])
def get_10_most_used_words():
    comment_ids = get_agg_comment_list(30, 100)
    c = get_most_common_words(comment_ids, 100, 10)
    return jsonify([word[0] for word in c])

@app.route("/mostusedwords", methods=['GET'])
def get_most_used_words_all_comments():
    comment_ids = get_agg_comment_list(10)
    for c in comment_ids:
        comments = recurse_comment_list(c)
    c = Counter(comments).most_common(25)
    return jsonify([word[0] for word in c])

if __name__=='__main__':
    app.run()