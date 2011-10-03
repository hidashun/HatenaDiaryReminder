# -*- coding: utf-8 -*-
"""
はてなダイアリーに日記を1日書いていなければ
Firefoxを開いて書くように促す

使い方:
    python hatenadiarireminder.py ユーザ名 パスワード

- lxml が必要
- cron で一定時間毎に実行するのを想定
- Mac OS X用 (open_hatena_diary メソッドを書き換えれば他OSでも使用可能)
"""

import os
import urllib2
import urllib
import cookielib
from datetime import datetime, timedelta
from lxml import etree, html
from urllib2 import URLError

class HatenaDiaryReminder:
    """はてなのユーザ名、パスワードを渡して生成"""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.opener = self.hatena_opener()

    def hatena_opener(self):
        """はてなにログインした状態の opener を返す"""
        
        cookiejar = cookielib.CookieJar()
        cookiejarhdr = urllib2.HTTPCookieProcessor(cookiejar)
        opener = urllib2.build_opener(cookiejarhdr)
    
        loginurl = 'https://www.hatena.ne.jp/login'
    
        postdata = {}
        postdata['name'] = self.username
        postdata['password'] = self.password
        params = urllib.urlencode(postdata)
    
        try:
            opener.open(loginurl, params).read()
        except urllib2.URLError:
            return None
        
        return opener
    
    def fetch_article_rss(self):
        """はてなダイアリーの記事RSSを取得する"""
        
        try:
            result = self.opener.open(
                'http://d.hatena.ne.jp/%s/rss' % self.username
            )
        except AttributeError:
            return u''
        
        return result.read()
    
    def fetch_draftlist_html(self):
        """はてなダイアリーの下書き一覧を取得する"""
        
        if self.opener == None:
            return u''
        try:
            conn = self.opener.open(
                'http://d.hatena.ne.jp/%s/draftlist' % self.username
            )
        except URLError:
            return u''
        return unicode(conn.read(), 'euc-jp')
    
    def open_hatena_diary(self):
        """Firefoxで下書き作成ページを開く(要ログイン)"""
        
        command_str = '''
        open -a firefox http://d.hatena.ne.jp/%s/draft
        ''' % self.username
        os.system(command_str)
    
    def run(self, force=False):
        """最近記事を書いていなければはてなダイアリーを開く"""
        
        statuslist = []
        
        rss = self.fetch_article_rss()
        statuslist.append(
            self.not_posted_lately(self.get_lastest_article_date(rss))
        )
        
        page = self.fetch_draftlist_html()
        statuslist.append(
            self.not_posted_lately(self.get_latest_draft_date(page))
        )
        
        print statuslist
        if self.should_remind(statuslist) or force == True:
            self.open_hatena_diary()
    
    @classmethod
    def get_lastest_article_date(cls, xmlstr):
        """最新の記事の投稿日時を取得する"""
        
        try:
            root = etree.fromstring(xmlstr)
        except etree.XMLSyntaxError:
            return datetime.now()
        
        latest_post = root.xpath(
            '''//rdf:RDF/rss:item/dc:date/text()''',
            namespaces={
                    'rss': 'http://purl.org/rss/1.0/',
                    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                    'content': 'http://purl.org/rss/1.0/modules/content/',
                    'dc': 'http://purl.org/dc/elements/1.1/'
            }
        )[0]
        if len(latest_post) == 10:
            latest = datetime.strptime(latest_post, '%Y-%m-%d')
        else:
            latest = datetime.strptime(latest_post, '%Y-%m-%dT%H:%M:%S+09:00')
        
        return latest
    
    @classmethod
    def get_latest_draft_date(cls, page):
        """最新の下書きの更新日時を取得する"""
        try:
            root = html.fromstring(page)
        except etree.XMLSyntaxError:
            return datetime.now()
        
        drafts = root.cssselect('''table.table-list > tbody > tr''')
    
        if len(drafts) < 1:
            return None
        
        latest = drafts[0].cssselect('td::nth-child(4)')[0].text
        
        return datetime.strptime(latest, '%Y-%m-%d %H:%M:%S')
    
    @classmethod
    def not_posted_lately(cls, latest):
        """1日以内に記事か下書きを書いたか"""
        
        return timedelta(days=1) < datetime.now() - latest
    
    @classmethod
    def should_remind(cls, statuslist):
        """記事も下書きも書いていなければTrue"""
        
        return all(statuslist)

if __name__ == '__main__':
    import sys
    ARGVS = sys.argv
    if len(sys.argv) < 2:
        print 'Usage: # python %s username password' % ARGVS[0]
        quit()
    USERNAME = ARGVS[1]
    PASSWORD = ARGVS[2]
    REMINDER = HatenaDiaryReminder(USERNAME, PASSWORD)
    REMINDER.run()