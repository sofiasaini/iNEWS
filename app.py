# doing necessary imports

import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
import os, ssl
from json import loads
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
    ssl._create_default_https_context = ssl._create_unverified_context

script_url = 'http://www.webscrapingfordatascience.com/readability/Readability.js'
get_article_cmd = requests.get(script_url).text
get_article_cmd += '''
var documentClone = document.cloneNode(true);
var loc = document.location;
var uri = {
  spec: loc.href,
  host: loc.host,
  prePath: loc.protocol + "//" + loc.host,
  scheme: loc.protocol.substr(0, loc.protocol.indexOf(":")),
  pathBase: loc.protocol + "//" + loc.host + 
            loc.pathname.substr(0, loc.pathname.lastIndexOf("/") + 1)
};
var article = new Readability(uri, documentClone).parse();
return JSON.stringify(article);
'''

driver = webdriver.Chrome(ChromeDriverManager().install())
driver.implicitly_wait(10)


def index():
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
            db = dbConn['newsDB'] # connecting to the database called crawlerDB
            table = db["news"]
            news_url = "https://news.google.com" # preparing the URL to search the product on flipkart
            uClient = uReq(news_url) # requesting the webpage from the internet
            news_url = uClient.read() # reading the webpage
            uClient.close() # closing the connection to the web server
            news_html = bs(news_url, "html.parser") # parsing the webpage as HTML
            for news_tag in news_html.select('article > h3 > a'):
                article_name = news_tag.contents
                article_link = "https://news.google.com/" + news_tag['href']
                print(article_name)
                print(article_link)
                print()
                driver.get(article_link)

                print('Injecting script')
                returned_result = driver.execute_script(get_article_cmd)

                # Convert JSON string to Python dictionary
                article = loads(returned_result)
                if not article:
                    # Failed to extract article, just continue
                    continue

                # Retrieve the final, non-Google URL
                news_url = driver.current_url
                # Add in the url
                article['url'] = news_url
                # Remove 'uri' as this is a dictionary on its own
                del article['uri']

                table.insert_one(article)
        except Exception as e:
            print(e)
            return 'something is wrong'


if __name__ == "__main__":
    index()
