import pytest
from django.urls import reverse
from library.models import BookExchange, StatusBook


@pytest.mark.django_db
def test_index_view_lists_books(client, book_factory, profile_factory):
    owner = profile_factory()
    book1 = book_factory(owner=owner)
    book2 = book_factory(owner=owner)

    response = client.get(reverse("index"))

    assert response.status_code == 200
    assert "index.html" in [t.name for t in response.templates]
    books = response.context["book_list"]
    assert len(books) == 2
    assert books[0] == book2  # Assuming order by -id
    assert books[1] == book1

@pytest.mark.django_db
def test_index_view_lists_books_none(client, book_factory, profile_factory):
    response = client.get(reverse("index"))

    assert response.status_code == 200
    assert "index.html" in [t.name for t in response.templates]
    books = response.context["book_list"]
    assert len(books) == 0