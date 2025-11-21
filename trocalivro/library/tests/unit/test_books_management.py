"""
Testes unitários para o service de gerenciamento de livros.

Este módulo testa as funcionalidades relacionadas ao gerenciamento de livros:
- Adição de novos livros
- Processamento de imagens de livros
- Busca de livros por título ou autor
- Validação de dados de entrada
- Tratamento de erros
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

from library.services.books_management_service import (
    add_new_book,
    display_book_image,
    search_books,
    BookAdditionError
)
from library.models import Book, StatusBook


@pytest.mark.django_db
def test_add_new_book_creates_book_successfully(profile_factory):
    """Testa a criação bem-sucedida de um livro com dados válidos"""
    profile = profile_factory()
    book_data = {
        'title': 'O Senhor dos Anéis',
        'author': 'J.R.R. Tolkien',
        'description': 'Um épico de fantasia',
        'genre': 'Fantasia'
    }

    book = add_new_book(book_data, profile)

    assert book.id is not None
    assert book.title == 'O Senhor dos Anéis'
    assert book.author == 'J.R.R. Tolkien'
    assert book.description == 'Um épico de fantasia'
    assert book.genre == 'Fantasia'
    assert book.owner == profile
    assert book.status == StatusBook.AVAILABLE.value

@pytest.mark.django_db
def test_add_new_book_with_image(profile_factory):
    """Testa a criação de livro com imagem"""
    profile = profile_factory()
    book_data = {
        'title': 'Harry Potter',
        'author': 'J.K. Rowling',
        'description': 'Livro de magia',
        'genre': 'Fantasia'
    }
    
    image_file = SimpleUploadedFile(
        "book_cover.jpg",
        b"fake image content",
        content_type="image/jpeg"
    )

    book = add_new_book(book_data, profile, book_image=image_file)

    assert book.title == 'Harry Potter'
    assert book.image is not None
    assert book.image.name.endswith('.jpg')

@pytest.mark.django_db
def test_add_new_book_raises_error_with_invalid_data(profile_factory):
    """Testa se BookAdditionError é lançada com dados inválidos"""
    profile = profile_factory()
    book_data = {
        'title': '',  # Campo obrigatório vazio
        'author': 'Autor Teste',
        'description': 'Descrição teste'
    }

    with pytest.raises(BookAdditionError) as excinfo:
        add_new_book(book_data, profile)
    
    assert "Dados do livro inválidos" in str(excinfo.value)


@pytest.mark.django_db
def test_add_new_book_raises_error_missing_required_fields(profile_factory):
    """Testa erro com campos obrigatórios ausentes"""
    profile = profile_factory()
    book_data = {
        'author': 'Autor Teste'
        # title e description ausentes
    }

    with pytest.raises(BookAdditionError):
        add_new_book(book_data, profile)


def test_display_book_image_with_valid_image():
    """Testa o processamento de imagem válida"""
    book = Book()
    book.image.name = "library/static/images/cover.jpg"

    result = display_book_image(book)

    assert result.image_display_url == "images/cover.jpg"


def test_display_book_image_without_image():
    """Testa o processamento quando não há imagem"""
    book = Book()
    book.image = None

    result = display_book_image(book)

    assert result.image_display_url == "images/no-image.png"


def test_display_book_image_with_empty_image():
    """Testa o processamento com imagem vazia"""
    book = Book()
    book.image.name = ""

    result = display_book_image(book)

    assert result.image_display_url == "images/no-image.png"


def test_display_book_image_with_different_path():
    """Testa o processamento com caminho diferente"""
    book = Book()
    book.image.name = "other/path/images/book.png"

    result = display_book_image(book)

    assert result.image_display_url == "other/path/images/book.png"


@pytest.mark.django_db
def test_search_books_by_title(book_factory, profile_factory):
    """Testa a busca de livros por título"""
    profile = profile_factory()
    book1 = book_factory(title="Harry Potter", author="J.K. Rowling", owner=profile)
    book2 = book_factory(title="Senhor dos Anéis", author="Tolkien", owner=profile)
    book3 = book_factory(title="Dom Casmurro", author="Machado", owner=profile)

    results = search_books("Harry")

    assert len(results) == 1
    assert results[0].id == book1.id
    assert results[0].title == "Harry Potter"


@pytest.mark.django_db
def test_search_books_by_author(book_factory, profile_factory):
    """Testa a busca de livros por autor"""
    profile = profile_factory()
    book1 = book_factory(title="Harry Potter", author="J.K. Rowling", owner=profile)
    book2 = book_factory(title="Fantastic Beasts", author="J.K. Rowling", owner=profile)
    book3 = book_factory(title="Dom Casmurro", author="Machado", owner=profile)

    results = search_books("J.K. Rowling")

    assert len(results) == 2
    book_ids = [book.id for book in results]
    assert book1.id in book_ids
    assert book2.id in book_ids


@pytest.mark.django_db
def test_search_books_case_insensitive(book_factory, profile_factory):
    """Testa se a busca é case-insensitive"""
    profile = profile_factory()
    book = book_factory(title="Harry Potter", author="J.K. Rowling", owner=profile)

    results = search_books("harry potter")

    assert len(results) == 1
    assert results[0].id == book.id


@pytest.mark.django_db
def test_search_books_partial_match(book_factory, profile_factory):
    """Testa busca com correspondência parcial"""
    profile = profile_factory()
    book = book_factory(title="O Senhor dos Anéis", author="Tolkien", owner=profile)

    results = search_books("Senhor")

    assert len(results) == 1
    assert results[0].id == book.id


@pytest.mark.django_db
def test_search_books_empty_query():
    """Testa busca com query vazia"""
    results = search_books("")

    assert len(results) == 0


@pytest.mark.django_db
def test_search_books_no_matches(book_factory, profile_factory):
    """Testa busca sem resultados"""
    profile = profile_factory()
    book_factory(title="Harry Potter", author="J.K. Rowling", owner=profile)

    results = search_books("Game of Thrones")

    assert len(results) == 0


@pytest.mark.django_db
def test_search_books_processes_images(book_factory, profile_factory):
    """Testa se a busca processa as imagens dos livros encontrados"""
    profile = profile_factory()
    book = book_factory(title="Test Book", author="Test Author", owner=profile)

    results = search_books("Test")

    assert len(results) == 1
    assert hasattr(results[0], 'image_display_url')
    assert results[0].image_display_url is not None


@pytest.mark.django_db
def test_search_books_by_title_and_author(book_factory, profile_factory):
    """Testa busca que pode encontrar por título ou autor"""
    profile = profile_factory()
    book1 = book_factory(title="Tolkien Biography", author="Someone Else", owner=profile)
    book2 = book_factory(title="Random Book", author="J.R.R. Tolkien", owner=profile)
    book3 = book_factory(title="Another Book", author="Other Author", owner=profile)

    results = search_books("Tolkien")

    assert len(results) == 2
    book_ids = [book.id for book in results]
    assert book1.id in book_ids  # Encontrado pelo título
    assert book2.id in book_ids  # Encontrado pelo autor
    assert book3.id not in book_ids