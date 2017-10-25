#!/usr/bin/env python2.7

from nltk import pos_tag, word_tokenize
from nltk.corpus import wordnet as wn
import requests
import re
from bleach import clean
from bs4 import BeautifulSoup
from pattern.en import lexeme, conjugate, tenses
import json
from utils import get_morphological_variants, search_in_line, score_answer


def answer_google(processed_question):
	question, questioning_word, morphed_variants = processed_question
	search_term = "+".join(question.split(' '))
	headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
	}
	results = requests.get("http://www.google.com/search?q=" + search_term, headers)
	items = BeautifulSoup(results.text, 'html5lib').find_all('h3', class_='r')[:3]
	url_found = ""
	line_found = ""
	answer = None
	answer_score = 0.0

	for i, item in enumerate(items):
		try:
			a_tag = item.find('a')
			link = a_tag['href'][7:] if 'href' in a_tag.attrs else None
			link = link if 'http' in link else None
			link = a_tag['onmousedown'].split('data-href="')[1].split('"')[0] if link == None and 'onmousedown' in a_tag.attrs else link
			if link:
				j = 0
				link = link.split('&')[0]
				link = "http://" + link[8:] if 'https://' in link else link
				page = requests.get(link)
				soup = BeautifulSoup(page.text, 'html5lib')
				[x.extract() for x in soup.find_all('script')]
				[x.extract() for x in soup.find_all('style')]
				[x.extract() for x in soup.find_all('ul')]
				[x.extract() for x in soup.find_all('ol')]
				text = soup.text.encode('ascii', 'ignore')
				text = clean(text, strip=True, tags=[])
				for line in text.replace('\n','.').split('.'):
					for m_v in morphed_variants:
						if search_in_line(m_v, line):
							score = score_answer(line, question, i + 1, j + 1, page.url)
							j += 1
							if score > answer_score:
								answer = (line, page.url)
								answer_score = score
		except Exception as e:
			print e
			pass

	if answer is not None:
		return ['Answer Found: "' + answer[0][:600] +'..."', 'At: ' + answer[1]]
	else:
		return None
