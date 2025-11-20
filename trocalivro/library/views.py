from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .services.exchange_service import create_exchange_request, BookExchangeError



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
    
# View para solicitar a troca de um livro
@login_required
def request_exchange_view(request, id):
    if request.method != 'POST':
        return redirect('index')

    try:
        create_exchange_request(book_id=id, requester_profile=request.user.profile)
    except PermissionDenied as e:
        messages.error(request, str(e))
        return redirect('index')
    except BookExchangeError as e:
        messages.warning(request, str(e))
        return redirect('index')
    else:
        messages.success(request, "Solicitação enviada com sucesso!")
        return redirect('send-books')