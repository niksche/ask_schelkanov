from django.http.response import HttpResponse
from django.core.paginator import Paginator

from django.shortcuts import render

# Create your views here.


questions = [
    {
        "id": {i},
        "title": f"Title {i}",
        "text": f"This is text for question with title {i}",
    } for i in range (10)
]

comments = [
    {
        "title": f"Title {i}",
        "text": f"This is text for question with title {i}",
    } for i in range (10)
]

def index(req):
    paginator = Paginator(questions, 5)
    page_number = req.GET.get('page')
    page_questions = paginator.get_page(page_number)
    return render(req, 'index.html', {'questions' : page_questions})


def ask(req): 
    return render(req, 'ask.html', {})

def login(req):
    return render(req, 'login.html', {})

def question(req, question_number=1): 
    question = questions[question_number]
    return render(req, 'question.html', {'question': question, 'comments': comments})

def register(req): 
    return render(req, 'signup.html', {})

def settings(req): 
    return render(req, 'settings.html', {})

def tag(req, key_tag="None"): 
    return render(req, 'tag.html', {'key_tag': key_tag})



