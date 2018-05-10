import requests
from bs4 import BeautifulSoup
import json

# json読み込み
with open("target.json", "r") as f:
    sites = json.load(f)
headers = sites["ua"]
now_on_page = 1
def get_contents(page=1):
    global sites, headers
    contents = []
    for site_name, site in sites.items():
        if site_name == "ua":
            continue
        if page==1:
            url = site["url"]
        else:
            url = site["url"] + site["next_url"].format(page)
        resp = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        posts = soup
        for i, e in enumerate(site["posts"]):
            if i == len(site["posts"]) - 1:
                posts = posts.find_all(e["elm"], attrs=e["attrs"])
            else:
                posts = posts.find(e["elm"], attrs=e["attrs"])
        for post in posts:
            content = post
            for i, e in enumerate(site["content"]):
                content = content.find(e["elm"], attrs=e["attrs"])
            c = {"site": "(" + site_name + ")"}
            for k in ["title", "link", "image"]:
                tmp_cont = content
                for i, e in enumerate(site[k]):
                    #print(k, e, tmp_cont)
                    if e is None:
                        if soup.head.find("link", rel="icon") is not None:
                            c[k] = soup.head.find("link", rel="icon").get("href")
                        else:
                            c[k] = ""
                    elif "key" in e:
                        c[k] = tmp_cont.get(e["key"])
                    elif "string" in e:
                        c[k] = tmp_cont.string
                    else:
                        tmp_cont = tmp_cont.find(e["elm"], attrs=e["attrs"])
            contents.append(c)

    # コンテンツ出力
    html = ""
    for content in contents:
        dom = """
        <div class="box" style="height: 350px; width:300px; display: inline-block;">
            <div class="thumbnail">
                <img width="100%" src=
        """ +\
        content["image"] +\
        """
                >
            </div>
            <div class="caption">
                <a href=
        """ +\
        content["link"] + ">" + content["title"] + content["site"] + "</a>" +\
        """
            </div>
        </div>
        """
        html += dom
    
    return html

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet")

@app.route('/')
def index():
    return render_template("index.html", contents=get_contents())

@socketio.on('continue')
def recv_cont():
    global now_on_page
    now_on_page += 1
    emit("return", get_contents(page=now_on_page))

if __name__ == "__main__":
    socketio.run(app)