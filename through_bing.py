#!/usr/bin/env python

from nltk import pos_tag, word_tokenize
from nltk.corpus import wordnet as wn
import requests
import re
from bleach import clean
from bs4 import BeautifulSoup
from pattern.en import lexeme, conjugate, tenses
import json
from utils import get_morphological_variants, search_in_line, score_answer
import time

def answer_bing(processed_question):
	start = time.time()
	question, questioning_word, morphed_variants = processed_question
	search_term = "+".join(question.split(' '))
	headers = {
		'Ocp-Apim-Subscription-Key': ""#Key is not working now
	}
	results = requests.get("https://api.cognitive.microsoft.com/bing/v5.0/search?q=" + search_term, headers=headers)
	items = json.loads(results.text)["webPages"]["value"][:3]
	if questioning_word is None or "you" in question or "your" in question:
		return ["I am a question answering bot that tries to answer your questions. Example: Who is Einstein? ", "I could not understand your question very well but here is a possible result: "  +  requests.get(items[0]["url"]).url]
	url_found = ""
	line_found = ""
	answer = None
	answer_score = 0.0
	flatten = lambda l: list(set([item for sublist in l for item in sublist]))
	for i, item in enumerate(items):
		try:
			link = item["url"]
			if link:
				j = 0
				page = requests.get(link)
				soup = BeautifulSoup(page.text.encode('ascii', 'ignore'), 'html5lib')
				if "en.wikipedia" in page.url:
					passages = [t.text.encode('ascii', 'ignore') for t in soup.find_all('p')]
					texts = []
					for p in passages:
						texts.extend(p.replace("?", ".").replace("!",".").split("."))
				else:
					[x.extract() for x in soup.find_all('script')]
					[x.extract() for x in soup.find_all('style')]
					[x.extract() for x in soup.find_all('ul')]
					[x.extract() for x in soup.find_all('ol')]
					texts = soup.text
					texts = clean(texts, strip=True, tags=[])
					texts = texts.replace('\n','.').replace('\t','.').replace("?", ".").replace("!",".").encode('ascii', 'ignore').split('.')
				for line in texts:
					for m_v in morphed_variants:
						if search_in_line(m_v, line):
							score = score_answer(line, question, i + 1, j + 1, page.url)
							j += 1
							if score > answer_score:
								answer = (line, page.url)
								answer_score = score
							if score >= 0.95:
								return ['"' + answer[0][:600] +'..." is my guess.', 'I found it at: ' + answer[1]]
							if int(time.time() - start) > 15:
								if answer is not None:
									return ['"' + answer[0][:600] +'..." is my guess.', 'I found it at: ' + answer[1]]
								else:
									return ["The answer could be at: " + requests.get(items[0]["url"]).url]
		except Exception as e:
			print e
			pass

	if answer is not None:
		return ['"' + answer[0][:600] +'..." is my guess.', 'I found it at: ' + answer[1]]
	else:
		return ["The answer could be at: " + requests.get(items[0]["url"]).url]

