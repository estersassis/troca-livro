from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import Http404
from .models import Book
from .services.exchange_service import (
    BookExchangeError,
    create_exchange_request,
    get_received_requests,
    get_sent_requests,
    respond_to_exchange_request,
)


def display_book_image(book):
    # Normaliza o caminho da imagem para ser usado pelo {% static %} no template.
    if getattr(book, "image", None) and book.image.name:
        image_path = book.image.name
        if "library/static/" in image_path:
            image_path = image_path.split("library/static/")[-1]
        book.image_display_url = image_path
    else:
        book.image_display_url = "images/no-image.png"
    return book

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
    sent_requests = get_sent_requests(request.user.profile)
    user_books = [display_book_image(exchange.book) for exchange in sent_requests]
    return render(request, 'send_books.html', {'user_books': user_books})

@login_required
def received_books(request):
    if request.method == "POST":
        exchange_id = request.POST.get("exchange_id")
        action = request.POST.get("action")
        message_text = request.POST.get("message", "")
        try:
            exchange_id = int(exchange_id)
            respond_to_exchange_request(
                exchange_id=exchange_id,
                owner_profile=request.user.profile,
                action=action,
                message=message_text,
            )
        except (TypeError, ValueError):
            messages.warning(request, "Solicitação inválida.")
        except BookExchangeError as e:
            messages.warning(request, str(e))
        else:
            if action == "accept":
                messages.success(request, "Solicitação aceita com sucesso.")
            else:
                messages.success(request, "Solicitação rejeitada.")
        return redirect("received-books")

    received_requests = get_received_requests(request.user.profile)
    user_books = []
    for exchange in received_requests:
        book = display_book_image(exchange.book)
        user_books.append(
            {
                "book": book,
                "requester_name": exchange.requester.firstname,
                "exchange_id": exchange.id,
                "message": exchange.message,
                "status": exchange.status,
            }
        )
    return render(request, 'received_books.html', {'user_books': user_books})

def book_detail_view(request, id):
    try:
        book = Book.objects.get(id=id)
    except Book.DoesNotExist:
        raise Http404("Livro não encontrado.")

    book_info = {
        "book": display_book_image(book),
        "user": request.user.profile if request.user.is_authenticated else None,
    }
    return render(request, 'book_detail.html', {'book_info': book_info})

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
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})
