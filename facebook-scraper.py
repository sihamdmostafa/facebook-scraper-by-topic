import getpass
import calendar
import os
import platform
import sys
import time
import urllib.request
import numpy as np
import gensim 
from gensim.models import Word2Vec
from bson.objectid import ObjectId

import pymongo
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["facebook"]
posts = mydb["posts"]
comments = mydb["comments"]

post = { "_id" : None, "page_name" : None, "page_url" : None, "post" : None }
comment = { "_id" : None, "page_name" : None , "page_url" : None , "commenter_id" : None , "comment" : None }

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

driver = None

page_name = "" #pagename
url = "" #url

total_scrolls = 10000
current_scrolls = 0
scroll_time = 5
old_height = 0


class DocSim:
    #calculates the similarity between two texts
    def __init__(self, w2v_model, stopwords=None):
        self.w2v_model = w2v_model
        self.stopwords = stopwords if stopwords is not None else []

    def vectorize(self, doc: str) -> np.ndarray:
        #computes the vector of a text
        doc = doc.lower()
        words = [w for w in doc.split(" ") if w not in self.stopwords]
        word_vecs = []
        for word in words:
            try:
                vec = self.w2v_model[word]
                word_vecs.append(vec)
            except KeyError:
                # Ignore, if the word doesn't exist in the vocabulary  
        vector = np.mean(word_vecs, axis=0)
        return vector

    def _cosine_sim(self, vecA, vecB):
        #computes the cos similarity between two vectors
        csim = np.dot(vecA, vecB) / (np.linalg.norm(vecA) * np.linalg.norm(vecB))
        if np.isnan(np.sum(csim)):
            return 0
        return csim

    def calculate_similarity(self, source_doc, target_docs):
        #calculate the vectors of two texts and the similarity between them
        results=[]
        source_vec = self.vectorize(source_doc)
        target_vec = self.vectorize(target_docs)
        sim_score = self._cosine_sim(source_vec, target_vec)
        return sim_score






def check_height():
    #allows to control the scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    return new_height != old_height

def scroll():
    #allow to scroll through the facebook page
    global old_height
    current_scrolls = 0

    while (True):
        try:
            if current_scrolls == total_scrolls:
                return
            old_height = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, scroll_time, 0.05).until(lambda driver: check_height())
            current_scrolls += 1            
        except TimeoutException:
            break

    return	

def login(email,password):
  #allows to authenticate in facebook
	try:
		global driver
		options = Options()
		options.add_argument("--disable-notifications")
		options.add_argument("--disable-infobars")
		options.add_argument("--mute-audio")
		try:
			driver = webdriver.Chrome(executable_path="./chromedriver", options=options)
		except:
			print("Latest driver required")
			exit()
		driver.get("https://en-gb.facebook.com")
		driver.maximize_window()
		driver.find_element_by_name('email').send_keys(email)
		driver.find_element_by_name('pass').send_keys(password)
		driver.find_element_by_id('loginbutton').click()
	except Exception as e:
		print("There's some error in log in.")
		print(sys.exc_info()[0])
		exit()

def scrape():
    #allow to scrap the page of facebook and extract the data needed 
    model = gensim.models.KeyedVectors.load_word2vec_format('./GoogleNews-vectors-negative300.bin', binary=True) #here we will use the pre-trained model of google
    sentence="death President Jacques Chirac" 
    similarity_with_texts=DocSim(model)
    threshold=0.8
	driver.get(url)
	scroll()
	txt=driver.find_elements_by_xpath("//a[@class='see_more_link']")
	try:
		for x in txt:
			x.send_keys(Keys.ENTER)
	except:
		pass
	
	txt=driver.find_elements_by_xpath("//a[@class='_5v47 fss']")
	try:
		for x in txt:
			x.send_keys(Keys.ENTER)
	except:
		pass

	j=0
	while True:
		try:
			a=driver.find_element_by_xpath("//a[@class='_4sxc _42ft']")
			a.send_keys(Keys.ENTER)
			j+=1
		except:
			print(j)
			break
			# pass
		
			
	txt=driver.find_elements_by_xpath("//div[contains(@class,'_5pbx userContent')]")
	try:
		for x in txt:
      		if(similarity_with_texts.calculate_similarity(sentence,x.text)>threshold):     
			  	post["_id"] = ObjectId() 
			  	post["page_name"] =  page_name
			  	post["page_url"] = url
			  	post["post"] = x.text
			  	InsertedResultObj = posts.insert_one(post)
	except:
		pass

	txt=driver.find_elements_by_xpath("//div[@class='_72vr']")
	try:
		for x in txt:
      		if(similarity_with_texts.calculate_similarity(sentence,x.text)>threshold):
			  	comment["_id"] = ObjectId()
			  	comment["page_name"] = page_name
			  	comment["page_url"] = url
			  	comment["commenter_id"] = a[0].get_attribute("href") #who made the comment
			  	comment["comment"] = x.text #what's in the comment
			  	InsertedResultObj = comments.insert_one(comment)
	except:
		pass


def main():
	email = ""
	password = ""
	login(email,password)
	scrape()
	driver.close()
 	        
if __name__ == '__main__':
	main()