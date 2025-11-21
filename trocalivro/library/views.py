from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm

from library.forms import EditProfile, SignUpForm
from library.models import Book
from .services.exchange_service import create_exchange_request, BookExchangeError

# Criado função responsavel por exibir imagens dos livros
def display_book_image(book):
    ...

def index(request):
    num_books = Book.objects.all().count()
    book_list = Book.objects.all()
   
    # Instanciado função para exibir a imagem dos livros
    for book in book_list:
       book.image_display_url = display_book_image(book) 

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
        book.image_display_url = display_book_image(book)

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
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})