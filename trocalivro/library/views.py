from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .forms import BookForm, EditProfile, SignUpForm
from .models import Book, StatusBook
from .services.exchange_service import BookExchangeError, create_exchange_request


def display_book_image(book):
    """Resolve a displayable path for the book image."""
    if book.image:
        return book.image.name
    return "images/no-image.png"


def index(request):
    books = Book.objects.all().order_by("-created_at")[:12]
    for book in books:
        book.image_display_url = display_book_image(book)
    return render(request, "index.html", {"book_list": books})


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data["firstname"]
            user.last_name = form.cleaned_data["lastname"]
            user.email = form.cleaned_data["email"]
            user.save()

            profile = user.profile
            profile.firstname = form.cleaned_data["firstname"]
            profile.lastname = form.cleaned_data["lastname"]
            profile.email = form.cleaned_data["email"]
            profile.phone_number = form.cleaned_data["phone_number"]
            profile.address = form.cleaned_data["address"]
            profile.save()

            messages.success(
                request, "Conta criada com sucesso! Faça login para continuar."
            )
            return redirect("login")
        messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile(request):
    user_books = Book.objects.filter(owner=request.user.profile)
    for book in user_books:
        book.image_display_url = display_book_image(book)
    return render(request, "profile.html", {"user_books": user_books})


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = EditProfile(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect("users-profile")
    else:
        form = EditProfile(instance=request.user.profile)

    return render(request, "edit_profile.html", {"form": form})


@login_required
def book_add(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.owner = request.user.profile
            book.status = StatusBook.AVAILABLE.value
            book.save()
            messages.success(request, "Livro cadastrado com sucesso.")
            return redirect("users-profile")
    else:
        form = BookForm()

    return render(request, "book_add.html", {"form": form})


@login_required
def my_books(request):
    return redirect("users-profile")


@login_required
def send_books(request):
    user_books = Book.objects.filter(owner=request.user.profile)
    for book in user_books:
        book.image_display_url = display_book_image(book)
    return render(request, "send_books.html", {"user_books": user_books})


@login_required
def received_books(request):
    user_books = Book.objects.filter(status=StatusBook.IN_EXCHANGE.value)
    for book in user_books:
        book.image_display_url = display_book_image(book)
    return render(request, "received_books.html", {"user_books": user_books})


def book_detail_view(request, id):
    book = get_object_or_404(Book, pk=id)
    book.image_display_url = display_book_image(book)
    return render(request, "book_detail.html", {"book": book})


def search_book(request):
    query = request.GET.get("q", "")
    found_books = Book.objects.filter(title__icontains=query) if query else []
    for book in found_books:
        book.image_display_url = display_book_image(book)
    return render(request, "index.html", {"book_list": found_books, "query": query})
    
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
