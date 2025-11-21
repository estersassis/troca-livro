from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import Http404

from library.forms import EditProfile, SignUpForm, BookForm
from .models import Book
from .services.exchange_service import (
    BookExchangeError,
    create_exchange_request,
    get_received_requests,
    get_sent_requests,
    respond_to_exchange_request,
)
from .services.books_management_service import add_new_book, search_books, display_book_image, BookAdditionError


def index(request):
    num_books = Book.objects.all().count()
    book_list = Book.objects.all()
   
    for book in book_list:
       book = display_book_image(book) 

    book_list = list(reversed(book_list))

    context = {
        'num_books': num_books,
        'book_list': book_list
    }

    return render(request, 'index.html', context=context)

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.profile.firstname=form.cleaned_data.get('firstname')
            user.profile.lastname=form.cleaned_data.get('lastname')
            user.profile.email=form.cleaned_data.get('email')
            user.profile.phone_number=form.cleaned_data.get('phone_number')
            user.profile.address=form.cleaned_data.get('address')    

            user.profile.save()

            password = form.cleaned_data.get('password1')
            if password:
                user.set_password(password)
                user.save() # Save the user again to update the password hash

            login(request, user)
            return redirect("/")
        else:
            print("Form Errors:", form.errors)
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile(request):
    user_books = Book.objects.filter(owner=request.user.profile)

    for book in user_books:
        book = display_book_image(book)

    user_books = list(reversed(user_books))

    return render(request, 'profile.html', {'user_books': user_books})

@login_required
def edit_profile(request):
    # Associando a sessão ao usuário.
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        # Atribuindo formulario a instancia do usuario
        form = EditProfile(request.POST, request.FILES, instance = profile)
        if form.is_valid():
            form.save()
        return redirect('users-profile')
    else:
        # independente se não for enviada
        form = EditProfile(instance=profile)

    # exibir na pagina de edição de perfil 
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def book_add(request):
    if request.method == 'POST':
        try:
            book = add_new_book(request.POST, request.user.profile, request.FILES.get('image'))
            return redirect('book-detail', id=book.pk)
        except BookAdditionError as e:
            messages.warning(request, str(e))
            return redirect('index')
    else:
        form = BookForm()
    return render(request, 'book_add.html', {'form':form})

@login_required
def send_books(request):
    sent_requests = get_sent_requests(request.user.profile)
    user_books = []
    for exchange in sent_requests:
        book_info = {
            'book': display_book_image(exchange.book),
            'status': exchange.status,
            'owner_name': exchange.book.owner.firstname,
            'exchange_id': exchange.id
        }
        user_books.append(book_info)
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
                "book": display_book_image(book),
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
    query = request.GET.get('q')
    if query:
        books = search_books(query)
    else:
        books = []
    return render(request, 'index.html', {'book_list': books})
    
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
