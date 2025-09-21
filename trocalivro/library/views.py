from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def display_book_image(book):
    ...

def index(request):
    ...


def signup(request):
    ...

@login_required
def profile(request):
    ...

@login_required
def edit_profile(request):
    ...

@login_required
def book_add(request):
    ...

@login_required
def my_books(request):
    ...

@login_required
def send_books(request):
    ...

@login_required
def received_books(request):
    ...

def book_detail_view(request, id):
    ...

def search_book(request):
    ...
    
# Função responsável por tratar as trocas entre os livros 
def request(request, id):
    ...