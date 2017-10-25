# askmefacts
A basic question-answering chatbot that uses information retrieval technique. (Under construction and a long way to go). I created an architechture similar to IBM Watson that utilizes both information retrieval and structured data approach to factoid answering. However, to implement my vision (AskMeFacts.jpg) without any funding and on my own seemed infeasible. Hence, I just put this out there on Facebook Messenger (using Heroku) to gauge interest. I got a lot of good user feedback.

I developed a voice-based version before this. You can see the demo at: https://www.youtube.com/watch?v=8SAP8t1e3Kg

# Installation
1. Install all dependencies into your system or a virtual environment(preferrable)

```pip install -r requirements.txt```

2. Install NLTK corpora required using nltk.download() from python shell

3. Run askmefacts.py. 

``` python askmefacts.py ```

4. Ask question and get answers.

``` 
Who is Einstein? 

Who is Bidhya Bhandari? 

When was Einstein born? 
```
