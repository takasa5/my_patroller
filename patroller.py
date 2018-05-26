import requests
from bs4 import BeautifulSoup
import json
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dateorder", help="ordered by date", action="store_true")
args = parser.parse_args()

# json読み込み
with open("target.json", "r", encoding="utf-8") as f:
    sites = json.load(f)
headers = sites["ua"]
now_on_page = 1
def get_contents(page=1):
    global sites, headers, args
    contents = []
    for site_name, site in sites.items():
        if site_name == "ua":
            continue
        if page==1:
            url = site["url"]
        else:
            url = site["url"] + site["next_url"].format(site["page_origin"] + page - 1)
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
            keys = ["title", "link", "image"]
            if args.dateorder:
                keys.append("date")
            for k in keys:
                tmp_cont = content
                for i, e in enumerate(site[k]):
                    if tmp_cont is None:
                        break
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
                    elif "all" in e:
                        tmp_cont = tmp_cont.find_all(e["elm"], attrs=e["attrs"])[e["all"]]
                    else:
                        if i == len(site[k]) - 1:
                            c[k] = tmp_cont
                        else:
                            tmp_cont = tmp_cont.find(e["elm"], attrs=e["attrs"])
            if args.dateorder:
                c["date"] = datetime.datetime.strptime(c["date"], site["date-format"])
            contents.append(c)

    if args.dateorder:
        contents = sorted(contents, key=lambda x: x["date"], reverse=True)
    # コンテンツ出力
    html = ""
    beforedate = None
    for content in contents:
        if beforedate == content["date"]:
            pass
        else:
            html += "<h2>" + str(content["date"].date()) + "</h2>" 
        beforedate = content["date"]
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