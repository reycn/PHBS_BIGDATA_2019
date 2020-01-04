import requests, time, os, csv, sys, json, importlib, re, datetime, time, random
import pandas as pd
from urllib.parse import quote
import os
import json as js


def head():
    # !IMPORTANT: user cookies needed! See ./data/cookies.json.template
    cookies_path = os.path.abspath('.') + '\\data\\cookies.json'
    # print(cookies_path)
    f = open(cookies_path, 'r')
    cookies = js.loads(f.read())
    # print(cookies[0])
    f.close()
    cookie_num = random.randint(0, len(cookies) - 1)
    cookie = cookies[cookie_num]["cookie"]
    # print('- Using account No.{}'.format(cookie_num))
    header = {
        'Cookie': cookie,
        'Referer': tweets_url,
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    return header


def get_data(url: str):
    try:
        r = requests.get(url, headers=head())
        if r.status_code == 418:
            while r.status_code == 200:
                print('- 418 occured, waiting...')
                time.sleep(random.random() * 3)
                return r.json()
        elif r.status_code == 200:
            return r.json()
        else:
            print('Unknown status_code' + str(r.status_code))
    except requests.ConnectionError as e:
        print("ERROR", e)


def fulltext(id: int):
    url = 'https://m.weibo.cn/statuses/extend?id=' + str(id)
    fulltext = html_text(get_data(url)["data"]["longTextContent"])
    return fulltext


def time_fix(time_string):
    now_time = datetime.datetime.now()
    if '刚刚' in time_string:
        return time_string.replace('刚刚', now_time.strftime('%Y-%m-%d %H:%M'))
    if '分钟前' in time_string:
        minutes = re.search(r'^(\d+)分钟', time_string).group(1)
        created_at = now_time - datetime.timedelta(minutes=int(minutes))
        return created_at.strftime('%Y-%m-%d %H:%M')
    if '小时前' in time_string:
        minutes = re.search(r'^(\d+)小时', time_string).group(1)
        created_at = now_time - datetime.timedelta(hours=int(minutes))
        return created_at.strftime('%Y-%m-%d %H:%M')
    if '今天' in time_string:
        return time_string.replace('今天', now_time.strftime('%Y-%m-%d'))
    if '昨天' in time_string:
        created_at = now_time - datetime.timedelta(days=1)
        return time_string.replace('昨天', created_at.strftime('%Y-%m-%d'))
    if '月' in time_string:
        time_string = time_string.replace('月', '-').replace('日', '')
        time_string = str(now_time.year) + '-' + time_string
        return time_string
    return time_string


def html_text(html: str):
    text = re.sub("<[^>]*>", "", html).strip()
    return text


def get_tweets(url: str):
    data = get_data(url)
    if data.__contains__("msg"):
        print('这里还没有内容')
        return (False)
    else:
        for tweet in data['data']['cards']:
            if tweet['card_type'] != 9:
                # print("This tweet is not from user, ignored.")
                pass
            else:
                try:
                    text = html_text(tweet['mblog']['text'])
                    id = int(tweet['mblog']['user']['id'])
                    if '全文' in text:
                        time.sleep(random.randint(1, 2))
                        # print('- Wait for a moment...')
                        print('- fetching fulltext of {}...'.format(id))
                        ftext = fulltext(id)
                        if ftext != "data":
                            text = ftext
                    topics = re.findall("#[^#]+#", text)
                    # text = re.sub("#[^#]+#", "", text) ## do not remove tags
                    text = text.replace('\n', '\s')
                    comments = []
                    if tweet['mblog'].__contains__('comment_summary'):
                        comments = [
                            i['text'] for i in tweet['mblog']
                            ['comment_summary']['comment_list']
                        ]
                    tweets.append([\
                                    id, \
                                    int(tweet['mblog']['id']), \
                                    time_fix(tweet['mblog']['created_at']), \
                                    int(tweet['mblog']['reposts_count']), \
                                    int(tweet['mblog']['comments_count']), \
                                    int(tweet['mblog']['attitudes_count']), \
                                    tweet['mblog']['user']['screen_name'], \
                                    text, \
                                    ])
                except Exception as e:
                    print(e)
    return tweets


def main(keywords: list):
    importlib.reload(sys)
    for keyword in keywords:
        print('*** {} ***'.format(keyword))
        keyword = quote(keyword)
        for page in range(0, 1):
            print('Fetching page {}      .................'.format(page))
            # API Example: https://m.weibo.cn/api/container/getIndex?type=all&queryVal=%E5%93%AA%E5%90%92&featurecode=20000320&luicode=10000011&lfid=106003type%3D1&title=%E5%93%AA%E5%90%92&containerid=100103type%3D1%26q%3D%E5%93%AA%E5%90%92&page_type=searchall&page=1
            tweets_url = 'https://m.weibo.cn/api/container/getIndex?type=all&queryVal={}&featurecode=20000320&luicode=10000011&lfid=106003type%3D1&title={}&containerid=100103type%3D1%26q%3D{}&page_type=searchall&page={}'.format(
                keyword, keyword, keyword, page)
            # print(tweets_url)
            result = get_tweets(tweets_url)
            if result == False:
                print('break')
                break
            else:
                time.sleep(random.random() * 6)

        print(tweets)
        df = pd.DataFrame(tweets,
                          columns=[
                              'uid', 'mid', 'time', 'f', 'c', 'l', 'user_name',
                              'content'
                          ])
        df.to_csv(os.path.abspath('.') + '\\data\\weibo.csv',
                  mode='a',
                  encoding="utf_8_sig",
                  index=False,
                  header=False)
    print('*** Task succesfully finished! ***')


if __name__ == "__main__":
    tweets_url = ""
    tweets = []
    keywords = [
        '社会', '国际', '科技', '科普', '数码', '财经', '股市', '明星', '综艺', '电视剧', '电影',
        '音乐', '汽车', '体育', '运动健身', '健康', '瘦身', '养生', '军事', '历史', '美女模特', '摄影',
        '情感', '搞笑', '辟谣', '正能量', '政务', '游戏', '旅游', '育儿', '校园', '美食', '房产',
        '家居', '星座', '读书', '三农', '设计', '艺术', '时尚', '美妆', '动漫', '宗教', '萌宠', '婚庆',
        '法律', '舞蹈', '收藏'
    ]
    main(keywords)