from flask import Flask, request, jsonify
import datetime
import requests
import re

app = Flask(__name__)

def get_top_stories(num):
    response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json').json()[:num]
    return response

def get_comment_list(sID):
    comments = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{sID}.json').json()
    if 'kids' in comments.keys():
        if len(comments['kids']) <=50:
            return comments['kids']
        return comments['kids'][:50]
    return []

def get_comment(cID):
    comment_text = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{cID}.json').json()['text']
    comment_text = re.sub(r'&quot;', ' ', comment_text)
    comment_text = re.sub(r'<p>', ' ', comment_text)
    comment_text = re.sub(r'&#x27;', '\'', comment_text)
    return comment_text

@app.route("/50comments", methods=['GET'])
def get_50_comments():
    comment_ids = []
    comments = []
    stories = get_top_stories(100)
    for s in stories:
        if len(comment_ids) >= 50:
            break
        comment_ids += get_comment_list(int(s))
    comments = [get_comment(c) for i,c in enumerate(comment_ids) if i<50]
    return jsonify(comments)

#@app.route("/10mostusedwords", methods=['GET'])

#@app.route("/mostusedwords", methods=['GET'])

if __name__=='__main__':
    app.run()