from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
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
    except BookExchangeError as e:
        messages.warning(request, str(e))
        return redirect('index')
    else:
        messages.success(request, "Solicitação enviada com sucesso!")
        return redirect('send-books')

def login_view(request):
    # Se o usuário já estiver logado, manda para o index ou perfil
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Bem-vindo de volta, {username}!")
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                messages.error(request, "Usuário ou senha inválidos.")
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})