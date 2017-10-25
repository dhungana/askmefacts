from nltk import pos_tag, word_tokenize
from nltk.corpus import wordnet as wn
import requests
import re
from bleach import clean
from bs4 import BeautifulSoup
from pattern.en import lexeme, conjugate, tenses
from os import system
import json

def score_answer(answer, question, position1, position2, url):
	question_words = question.lower().split(" ")
	answer_words = answer.lower().replace(",", " ").split()
	length = len(answer_words)
	urls = [("en.wikipedia", 1.0), ("nytimes", 0.5), ("bbc", 0.5),("facebook.com", -100.0)]
	reliability = 0.0
	for r_u in urls:
		if r_u[0] in url:
			reliability = r_u[1]
			break
	matches = 0.0
	for q in question_words:
		for a in answer_words:
			if q == a:
				matches += 1.0
				break

	score = (matches * 5.0/len(question_words) + 5.0/position1 + 5.0/position2 + reliability * 5.0 ) / (3.0 + 2.5 + 2.0 + 2.5)
	return score

def search_in_line(string, line):
	questioning_words = ["who", "what", "how", "when", "why", "where", "who", "which"]
	s_words = string.split(" ")
	l_words = line.replace(","," ").split(" ")
	if len(l_words) < len(s_words):
		return False
	counter = 0
	for l in l_words:
		if len(l) == 0:
			continue
		if s_words[counter].lower() == l.lower() or (len(s_words[counter]) > 3 and l.lower() in [s_words[counter].lower() + "s", s_words[counter].lower() + "ed"]) or s_words[counter].lower() in questioning_words:
			counter += 1
		elif "regex:" in s_words[counter] and l[0] in s_words[counter][6:]:
			counter += 1
		if counter == len(s_words):
			return True
	return False

def get_morphological_variants(questioning_word, morphed_front_keywords, morphed_verbs, morphed_back_keywords):
	if questioning_word in ["who", "what", "which"]:
		options1 = morphed_verbs + morphed_back_keywords
		options2 = morphed_back_keywords + morphed_verbs
		options3 = morphed_back_keywords + morphed_verbs + [["by"]]
	elif questioning_word in ["when", "where"]:
		regex = [["regex:0123456789"]] if questioning_word in "when" else [["regex:abcdefghijklmnopqrstuvwxyz"]]
		options1 = morphed_front_keywords +  morphed_verbs + morphed_back_keywords + [["in", "on", "at", "during"]] + regex
		options2 = []
		options3 = []
	else:
		options1 = morphed_front_keywords +  morphed_verbs + morphed_back_keywords 
		options2 = []
		options3 = []
	morphological_variants1 = []
	morphological_variants2 = []
	morphological_variants3 = []

	for options in options1:
		if len(morphological_variants1) is 0:
			morphological_variants1 = options
		else:
			new_morphological_variants1 = []
			for m_v in morphological_variants1:
				for o in options:
					new_morphological_variants1.append(m_v + " " + o)
			morphological_variants1 = new_morphological_variants1

	for options in options2:
		if len(morphological_variants2) is 0:
			morphological_variants2 = options
		else:
			new_morphological_variants2 = []
			for m_v in morphological_variants2:
				for o in options:
					new_morphological_variants2.append(m_v + " " + o)
			morphological_variants2 = new_morphological_variants2

	for options in options3:
		if len(morphological_variants3) is 0:
			morphological_variants3 = options
		else:
			new_morphological_variants3 = []
			for m_v in morphological_variants3:
				for o in options:
					new_morphological_variants3.append(m_v + " " + o)
			morphological_variants3 = new_morphological_variants3


	return morphological_variants1 + morphological_variants2 + morphological_variants3

def get_options(string):
	synsets = wn.synsets(string)
	if synsets and len(synsets) > 0:
		options = [str(lemma.name()).lower().replace('_', ' ') for lemma in synsets[0].lemmas()]
		if string.lower() in options:
			options.remove(string.lower())
		options = [string.lower()] + options
	else:
		options = [token]
	return list(set(options))


def get_reformulated_question_boolean(questioning_word, question):
	it_true_that = False
	if "it true that" in question:
		it_true_that = True
		question = question.replace("it true that", "")
		reformulated_question = " ".join(question.split(" ")[1:])
	question_words = question.split(" ")[1:]
	l = len(question_words)
	question = " ".join(question_words)
	tokenized_tagged = pos_tag(word_tokenize(question))
	front = []
	back = []
	noun_discontinued = False
	noun_start = False
	main_verb = None
	found = False
	passive = False
	for token, tag in tokenized_tagged:
		if found is False:
			for s in wn.synsets(token):
				for lemma in s.lemmas():
					if token == lemma.name() and s.pos()==u'v' and token.lower() == conjugate(token.lower(), tense="present", person=1, number="singular"):			
						main_verb = token
						if noun_start and not noun_discontinued:
							noun_discontinued = True
						found = True
						break
				if found:
					break
			if found:
				continue

		if noun_start:
			if noun_discontinued:
				back.append(token)
			elif bool(re.search(r"^NN", tag)):
				front.append(token)
			else:
				noun_discontinued = True
				back.append(token)
		elif bool(re.search(r"^NN", tag)):
			front.append(token)
			noun_start = True
		else:
			front.append(token)

	if len(back) == 0 and main_verb == None:
		for i in range(1, l):
			front = " ".join(question_words[:-i])
			back = " ".join(question_words[-i:])
			front_entities = search_wikidata(front)
			back_entities = search_wikidata(back)
			if len(front_entities) > 0 or len(back_entities) > 0:
				break
	else:
		front = " ".join(front)
		back = " ".join(back)
		front_entities = search_wikidata(front)
		back_entities = search_wikidata(back) if back is not "" else []
	if questioning_word is "do":
		reformulated_question = front + " " + main_verb + " " + back
	elif questioning_word is "does" and main_verb:
		main_verb = conjugate(main_verb, tense="present", person=3, number="singular")
		reformulated_question = front + " " + main_verb + " " + back
	elif questioning_word is "did" and main_verb:
		main_verb = conjugate(main_verb, tense="past", person=3, number="singular")
		reformulated_question = front + " " + main_verb + " " + back
	elif it_true_that:
		reformulated_question = reformulated_question
	elif main_verb:
		reformulated_question = front + " " + questioning_word + " " + main_verb + " " + back
	else:
		reformulated_question = front + " " + questioning_word + " " + back

	return reformulated_question

def pre_process(question):
	question = question.replace("?", "").replace(",", " ")
	questioning_words = ["who", "what", "how", "when", "why", "where", "who", "which", "is", "are", "was", "were", "do", "does", "did", "can"]

	question_front = []
	question_back = []
	questioning_word_found = False
	questioning_word = None
	for i, word in enumerate(question.split(" ")):
		for q_word in questioning_words:
			if questioning_word_found:
				question_front.append(word)
				break
			elif word.lower() == q_word:
				questioning_word = q_word
				questioning_word_found = True
				question_front.append(word)
				break
			elif word.lower() == q_word + "'s":
				questioning_word = q_word
				questioning_word_found = True
				question_front.append(word[:-2] + " is")
				break
		if not questioning_word_found:
			if i == 0:
				question_back.append(word.lower()) 
			else:
				question_back.append(word)
	if not questioning_word_found:
		return None, question

	if len(question_back) > 0:
		question = " ".join(question_front) + " " + " ".join(question_back)
	else:
		question = " ".join(question_front)

	if questioning_word in ["is", "are", "was", "were", "do", "does", "did", "can"]:
		question = get_reformulated_question_boolean(questioning_word, question)

	return questioning_word, question

def get_three_parts(question):
	questioning_words = ["who", "what", "how", "when", "why", "where", "who", "whom", "which"]
	tokenized_tagged = pos_tag(word_tokenize(question))
	first = []
	second = []
	third = []
	noun_discontinued = False
	noun_start = False
	verb_discontinued = False
	passive = False
	in_word = False
	main_verb = None

	for token, tag in tokenized_tagged:
		if bool(re.search(r"^V", tag)):
			main_verb = token

	if main_verb is None:
		for token, tag in tokenized_tagged:
			if wn.synsets(token, pos=wn.VERB):
				main_verb = token

	for i, (token, tag) in enumerate(tokenized_tagged):
		if not noun_start and not (bool(re.search(r"^NN", tag)) or bool(re.search(r"^CD", tag)) or bool(re.search(r"^IN", tag)) or bool(re.search(r"^RB", tag)) or bool(re.search(r"^JJ", tag)) or token.lower() in questioning_words):
			first.append(token)
		elif (bool(re.search(r"^NN", tag) or token.lower() in questioning_words)) and not noun_discontinued:
			noun_start = True
			first.append(token)
		elif noun_start and not verb_discontinued and main_verb == token:
			noun_discontinued = True
			second = [token]
		elif noun_discontinued and not token == main_verb:
			verb_discontinued = True

		if verb_discontinued and (bool(re.search(r"^NN", tag)) or bool(re.search(r"^CD", tag)) or bool(re.search(r"^IN", tag)) or bool(re.search(r"^RB", tag)) or bool(re.search(r"^JJ", tag))):
			third.append(token)
	
	#Passive to active
	if "by" in third and len(third) > 1:
		temp = first
		first = third
		third = temp
		first = first[1:]

	return first, second, third


def search_wikidata(string, item_or_property="item"):
	url = "https://www.wikidata.org/w/api.php?action=wbsearchentities&language=en&format=json&limit=3&type="+ item_or_property +"&search=" + string
	r = requests.get(url)
	d = r.json()
	if len(d['search']) is 0:
		return []
	return [(x["id"], x["label"], x.get("description", "")) for x in d['search']]
