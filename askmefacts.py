#!/usr/bin/env python
from utils import pre_process, get_reformulated_question_boolean, get_three_parts, get_options, get_morphological_variants
from through_google import answer_google
from through_bing import answer_bing
from nltk import pos_tag, word_tokenize
from nltk.corpus import wordnet as wn
from pattern.en import lexeme, conjugate, tenses

def answer_question(question):
	question = question.encode('ascii', 'ignore')
	questioning_word, question = pre_process(question)
	if questioning_word == None:
		processed_question = question, questioning_word, []
	else:
		front_keywords, main_verbs, back_keywords = get_three_parts(question)
		morphed_front_keywords = []
		for k in front_keywords:
			if wn.synsets(k, pos=wn.NOUN):
				options = get_options(k)
				if k.lower() in options:
					options.remove(k.lower())
					options = [k.lower()] + options
				morphed_front_keywords.append(options)
			else:
				morphed_front_keywords.append([k])

		morphed_verbs = []
		for v in main_verbs:
			if wn.synsets(v, pos=wn.VERB):
				options = get_options(v)
				flatten = lambda l: list(set([item for sublist in l for item in sublist]))
				options = flatten([lexeme(v)])
				if v.lower() in options:
					options.remove(v.lower())
					options = [v.lower()] + options
				morphed_verbs.append(options)
			else:
				morphed_verbs.append([v])
		

		morphed_back_keywords = []
		for k in back_keywords:
			if wn.synsets(k, pos=wn.NOUN):
				options = get_options(k)
				if k.lower() in options:
					options.remove(k.lower())
					options = [k.lower()] + options
				morphed_back_keywords.append(options)
			else:
				morphed_back_keywords.append([k])

		morphed_variants = get_morphological_variants(questioning_word, morphed_front_keywords, morphed_verbs, morphed_back_keywords)
		processed_question = (question, questioning_word, morphed_variants)
	
	# Bing API has expired.
	# print "Bing:"
	# try:
	# 	answer = answer_bing(processed_question)

	# 	if answer:
	# 		return answer + ["Another one?"]
	# except Exception as e:
	# 	print e

	# print "Google:"
	try:
		answer = answer_google(processed_question)
		if answer:
			return answer + ["Another one?"]
	except Exception as e:
		print e

	return ["Sorry. I am not ready to answer that question yet.","Another one?"]


def test():
	test_questions = ["Was Einstein born in Ulm?",
					  "Who designed the Eiffel Tower?",
					  "What is the tallest mountain?",
					  "How can you cook rice?",
					  "When did America become independent?",
					  "Why is the sky blue?",
					  "Where is Nepal?",
					  "Who is Trump?",
					  "Which country has the highest GDP?",
					  "Was Einstein born in 1879?",
					  "Was Einstein born in Germany?",
					  "Is it true that humans were created by God?",
					  "Is Bidhya Bhandari the current President of Nepal?", 
					  "Are humans living beings?",
					  "Do birds sing?",
					  "Does an ant have four legs?",
					  "Did Obama start Obamacare?",
					  "Can machines think like humans?",
					  ]

	for t_q in test_questions:
		print t_q
		answer = answer_question(t_q)
		print answer

def main():
	question = None
	print "Enter question:"
	while question != "quit":
		question = raw_input()
		print answer_question(question) 

if __name__ == '__main__':
	# test()
	main()
