from django.db import transaction
from library.models import Book, BookExchange, StatusBook
from library.forms import BookForm


class BookAdditionError(Exception):
    """Exceção de domínio para erros na adição de livros."""

    pass

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

@transaction.atomic
def add_new_book(book_data, owner_profile, book_image=None):
    form = BookForm(book_data)
    if not form.is_valid():
        raise BookAdditionError("Dados do livro inválidos.")

    book = form.save(commit=False)
    book.owner = owner_profile
    book.status = StatusBook.AVAILABLE.value

    if book_image:
        book.image = book_image

    book.save()
    return book

def search_books(query):
    books = Book.objects.filter(title__icontains=query)
    for book in books:
        book.image_display_url = display_book_image(book) 
    return books