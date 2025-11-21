import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from library.models import Book, StatusBook


@pytest.mark.django_db
def test_book_add_get_displays_form(client, user_factory, profile_factory):
    """Testa se o formulário de adicionar livro é exibido corretamente"""
    user = user_factory()
    profile = profile_factory(user=user)

    client.force_login(user)
    response = client.get(reverse("book-add"))

    assert response.status_code == 200
    assert "book_add.html" in [t.name for t in response.templates]
    assert "form" in response.context
    form = response.context["form"]
    assert hasattr(form, "fields")
    assert "title" in form.fields
    assert "author" in form.fields
    assert "description" in form.fields


@pytest.mark.django_db
def test_book_add_post_creates_book_successfully(client, user_factory, profile_factory):
    """Testa a criação bem-sucedida de um livro via POST"""
    user = user_factory()
    profile = profile_factory(user=user)

    client.force_login(user)
    response = client.post(
        reverse("book-add"),
        {
            "title": "O Senhor dos Anéis",
            "author": "J.R.R. Tolkien",
            "description": "Uma épica fantasia sobre a Terra-média",
            "genre": "Fantasia",
        },
    )

    # Verifica redirecionamento
    assert response.status_code == 302

    # Verifica se o livro foi criado
    book = Book.objects.get(title="O Senhor dos Anéis")
    assert book.author == "J.R.R. Tolkien"
    assert book.description == "Uma épica fantasia sobre a Terra-média"
    assert book.owner == profile
    assert book.status == StatusBook.AVAILABLE.value

    # Verifica redirecionamento para detalhes do livro
    assert response.url == reverse("book-detail", args=[book.pk])


@pytest.mark.django_db
def test_book_add_post_with_image(client, user_factory, profile_factory):
    """Testa a criação de livro com upload de imagem"""
    user = user_factory()
    profile = profile_factory(user=user)

    image_file = SimpleUploadedFile(
        "book_cover.jpg", b"fake image content", content_type="image/jpeg"
    )

    client.force_login(user)
    response = client.post(
        reverse("book-add"),
        {
            "title": "Harry Potter",
            "author": "J.K. Rowling",
            "description": "Livro de magia",
            "genre": "Fantasia",
            "image": image_file,
        },
    )

    assert response.status_code == 302

    book = Book.objects.get(title="Harry Potter")
    assert book.author == "J.K. Rowling"
    assert book.image is not None
    assert book.owner == profile


@pytest.mark.django_db
def test_book_add_post_with_invalid_data_redirects(
    client, user_factory, profile_factory
):
    """Testa comportamento com dados inválidos"""
    user = user_factory()
    profile = profile_factory(user=user)

    client.force_login(user)
    response = client.post(
        reverse("book-add"),
        {
            "title": "",  # Campo obrigatório vazio
            "author": "Autor Teste",
            "description": "Descrição",
        },
    )

    # Deve redirecionar para index com mensagem de erro
    assert response.status_code == 302
    assert response.url == reverse("index")

    # Verifica que nenhum livro foi criado
    assert not Book.objects.filter(author="Autor Teste").exists()


@pytest.mark.django_db
def test_book_detail_view_displays_book_info(client, book_factory, profile_factory):
    """Testa se os detalhes do livro são exibidos corretamente"""
    profile = profile_factory()
    book = book_factory(
        title="Dom Casmurro",
        author="Machado de Assis",
        description="Romance clássico brasileiro",
        genre="Romance",
        owner=profile,
        status=StatusBook.AVAILABLE.value,
    )

    response = client.get(reverse("book-detail", args=[book.id]))

    assert response.status_code == 200
    assert "book_detail.html" in [t.name for t in response.templates]

    book_info = response.context["book_info"]
    assert book_info["book"].id == book.id
    assert book_info["book"].title == "Dom Casmurro"
    assert book_info["book"].author == "Machado de Assis"
    assert book_info["user"] is None  # Usuário não autenticado


@pytest.mark.django_db
def test_book_detail_view_nonexistent_book_raises_404(client):
    """Testa se livro inexistente retorna 404"""
    response = client.get(reverse("book-detail", args=[9999]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_book_detail_view_processes_book_image(client, book_factory, profile_factory):
    """Testa se a imagem do livro é processada corretamente"""
    profile = profile_factory()
    book = book_factory(owner=profile)

    response = client.get(reverse("book-detail", args=[book.id]))

    assert response.status_code == 200
    book_info = response.context["book_info"]
    assert hasattr(book_info["book"], "image_display_url")


@pytest.mark.django_db
def test_search_book_with_query_finds_books(client, book_factory, profile_factory):
    """Testa busca de livros com query válida"""
    profile = profile_factory()
    book1 = book_factory(title="Harry Potter", author="J.K. Rowling", owner=profile)
    book2 = book_factory(title="Dom Casmurro", author="Machado de Assis", owner=profile)
    book3 = book_factory(title="O Hobbit", author="J.R.R. Tolkien", owner=profile)

    response = client.get(reverse("search-books"), {"q": "Harry"})

    assert response.status_code == 200
    assert "index.html" in [t.name for t in response.templates]

    book_list = response.context["book_list"]
    assert len(book_list) == 1
    assert book_list[0].id == book1.id
    assert book_list[0].title == "Harry Potter"


@pytest.mark.django_db
def test_search_book_by_author(client, book_factory, profile_factory):
    """Testa busca de livros por autor"""
    profile = profile_factory()
    book1 = book_factory(title="Harry Potter", author="J.K. Rowling", owner=profile)
    book2 = book_factory(title="Fantastic Beasts", author="J.K. Rowling", owner=profile)
    book3 = book_factory(title="O Hobbit", author="Tolkien", owner=profile)

    response = client.get(reverse("search-books"), {"q": "J.K. Rowling"})

    assert response.status_code == 200
    book_list = response.context["book_list"]
    assert len(book_list) == 2

    book_ids = [book.id for book in book_list]
    assert book1.id in book_ids
    assert book2.id in book_ids


@pytest.mark.django_db
def test_search_book_case_insensitive(client, book_factory, profile_factory):
    """Testa se a busca é case-insensitive"""
    profile = profile_factory()
    book = book_factory(title="Harry Potter", author="J.K. Rowling", owner=profile)

    response = client.get(reverse("search-books"), {"q": "harry potter"})

    assert response.status_code == 200
    book_list = response.context["book_list"]
    assert len(book_list) == 1
    assert book_list[0].id == book.id


@pytest.mark.django_db
def test_search_book_no_results(client, book_factory, profile_factory):
    """Testa busca sem resultados"""
    profile = profile_factory()
    book_factory(title="Harry Potter", author="J.K. Rowling", owner=profile)

    response = client.get(reverse("search-books"), {"q": "Game of Thrones"})

    assert response.status_code == 200
    book_list = response.context["book_list"]
    assert len(book_list) == 0


@pytest.mark.django_db
def test_search_book_empty_query_returns_empty_list(
    client, book_factory, profile_factory
):
    """Testa busca com query vazia"""
    profile = profile_factory()
    book_factory(title="Livro Teste", author="Autor Teste", owner=profile)

    response = client.get(reverse("search-books"))  # Sem parâmetro q

    assert response.status_code == 200
    book_list = response.context["book_list"]
    assert len(book_list) == 0


@pytest.mark.django_db
def test_search_book_whitespace_query_returns_empty_list(
    client, book_factory, profile_factory
):
    """Testa busca com query só com espaços"""
    profile = profile_factory()
    book_factory(title="Livro Teste", author="Autor Teste", owner=profile)

    response = client.get(reverse("search-books"), {"q": "   "})

    assert response.status_code == 200
    book_list = response.context["book_list"]
    assert len(book_list) == 0


@pytest.mark.django_db
def test_search_book_processes_book_images(client, book_factory, profile_factory):
    """Testa se a busca processa as imagens dos livros"""
    profile = profile_factory()
    book = book_factory(title="Livro Teste", author="Autor Teste", owner=profile)

    response = client.get(reverse("search-books"), {"q": "Livro"})

    assert response.status_code == 200
    book_list = response.context["book_list"]
    assert len(book_list) == 1
    assert hasattr(book_list[0], "image_display_url")


@pytest.mark.django_db
def test_search_book_partial_matches(client, book_factory, profile_factory):
    """Testa busca com correspondências parciais"""
    profile = profile_factory()
    book1 = book_factory(title="O Senhor dos Anéis", author="Tolkien", owner=profile)
    book2 = book_factory(title="As Duas Torres", author="Tolkien", owner=profile)
    book3 = book_factory(title="Harry Potter", author="J.K. Rowling", owner=profile)

    # Busca por "Senhor" deve encontrar só o primeiro livro
    response = client.get(reverse("search-books"), {"q": "Senhor"})

    assert response.status_code == 200
    book_list = response.context["book_list"]
    assert len(book_list) == 1
    assert book_list[0].id == book1.id

    # Busca por "Tolkien" deve encontrar os dois primeiros
    response = client.get(reverse("search-books"), {"q": "Tolkien"})

    assert response.status_code == 200
    book_list = response.context["book_list"]
    assert len(book_list) == 2
    book_ids = [book.id for book in book_list]
    assert book1.id in book_ids
    assert book2.id in book_ids


@pytest.mark.django_db
def test_search_book_combines_title_and_author_results(
    client, book_factory, profile_factory
):
    """Testa busca que combina resultados por título e autor"""
    profile = profile_factory()
    book1 = book_factory(
        title="Tolkien Biography", author="Someone Else", owner=profile
    )
    book2 = book_factory(title="Random Book", author="J.R.R. Tolkien", owner=profile)
    book3 = book_factory(title="Another Book", author="Other Author", owner=profile)

    response = client.get(reverse("search-books"), {"q": "Tolkien"})

    assert response.status_code == 200
    book_list = response.context["book_list"]
    assert len(book_list) == 2

    book_ids = [book.id for book in book_list]
    assert book1.id in book_ids  # Encontrado pelo título
    assert book2.id in book_ids  # Encontrado pelo autor
    assert book3.id not in book_ids


@pytest.mark.django_db
def test_book_add_redirects_to_book_detail_on_success(
    client, user_factory, profile_factory
):
    """Testa se após criar livro com sucesso, redireciona para detalhes"""
    user = user_factory()
    profile = profile_factory(user=user)

    client.force_login(user)
    response = client.post(
        reverse("book-add"),
        {
            "title": "Novo Livro",
            "author": "Novo Autor",
            "description": "Nova descrição",
            "genre": "Romance",
        },
    )

    book = Book.objects.get(title="Novo Livro")
    assert response.status_code == 302
    assert response.url == reverse("book-detail", args=[book.pk])

    # Testa se consegue acessar a página de detalhes
    detail_response = client.get(response.url)
    assert detail_response.status_code == 200
    assert detail_response.context["book_info"]["book"].title == "Novo Livro"
