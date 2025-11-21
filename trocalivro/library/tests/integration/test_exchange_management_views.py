import pytest
from django.urls import reverse

from library.models import StatusBook
from library.services.exchange_service import create_exchange_request


@pytest.mark.django_db
def test_send_books_lists_sent_requests(
    client, user_factory, profile_factory, book_factory
):
    user = user_factory()
    requester_profile = profile_factory(user=user)
    owner = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)
    create_exchange_request(book_id=book.id, requester_profile=requester_profile)

    client.force_login(user)
    response = client.get(reverse("send-books"))

    assert response.status_code == 200
    assert "send_books.html" in [t.name for t in response.templates]
    user_books = response.context["user_books"]
    assert len(user_books) == 1
    assert user_books[0]["book"] == book


@pytest.mark.django_db
def test_send_books_requires_authentication(client):
    response = client.get(reverse("send-books"))

    assert response.status_code == 302
    assert "/login" in response.url


@pytest.mark.django_db
def test_received_books_lists_requests_and_accepts(
    client, user_factory, profile_factory, book_factory
):
    owner_user = user_factory()
    owner_profile = profile_factory(user=owner_user)
    requester_profile = profile_factory()
    book = book_factory(owner=owner_profile, status=StatusBook.AVAILABLE.value)
    exchange = create_exchange_request(
        book_id=book.id, requester_profile=requester_profile
    )

    client.force_login(owner_user)
    response = client.get(reverse("received-books"))
    assert response.status_code == 200
    assert "received_books.html" in [t.name for t in response.templates]
    user_books = response.context["user_books"]
    assert user_books[0]["book"] == book
    assert user_books[0]["requester_name"] == requester_profile.firstname

    post_response = client.post(
        reverse("received-books"),
        {"exchange_id": exchange.id, "action": "accept", "message": "Vamos trocar"},
    )
    assert post_response.status_code == 302
    book.refresh_from_db()
    exchange.refresh_from_db()
    assert exchange.status == StatusBook.UNAVAILABLE.value
    assert exchange.message == "Vamos trocar"
    assert book.status == StatusBook.UNAVAILABLE.value


@pytest.mark.django_db
def test_received_books_rejects_request(
    client, user_factory, profile_factory, book_factory
):
    owner_user = user_factory()
    owner_profile = profile_factory(user=owner_user)
    requester_profile = profile_factory()
    book = book_factory(owner=owner_profile, status=StatusBook.AVAILABLE.value)
    exchange = create_exchange_request(
        book_id=book.id, requester_profile=requester_profile
    )

    client.force_login(owner_user)
    response = client.post(
        reverse("received-books"),
        {"exchange_id": exchange.id, "action": "reject", "message": "Talvez depois"},
    )

    assert response.status_code == 302
    exchange.refresh_from_db()
    book.refresh_from_db()
    assert exchange.status == StatusBook.AVAILABLE.value
    assert exchange.message == "Talvez depois"
    assert book.status == StatusBook.AVAILABLE.value


@pytest.mark.django_db
def test_received_books_prevents_unauthorized_response(
    client, user_factory, profile_factory, book_factory
):
    owner_profile = profile_factory()
    requester_user = user_factory()
    requester_profile = profile_factory(user=requester_user)
    other_profile = profile_factory()
    book = book_factory(owner=owner_profile, status=StatusBook.AVAILABLE.value)
    exchange = create_exchange_request(book_id=book.id, requester_profile=other_profile)

    client.force_login(requester_user)
    response = client.post(
        reverse("received-books"),
        {"exchange_id": exchange.id, "action": "accept"},
    )

    assert response.status_code == 302
    exchange.refresh_from_db()
    assert exchange.status == StatusBook.IN_EXCHANGE.value


@pytest.mark.django_db
def test_book_detail_view_renders_book_info(
    client, user_factory, profile_factory, book_factory
):
    user = user_factory()
    profile = profile_factory(user=user)
    book = book_factory(owner=profile, status=StatusBook.AVAILABLE.value)

    client.force_login(user)
    response = client.get(reverse("book-detail", args=[book.id]))

    assert response.status_code == 200
    assert "book_detail.html" in [t.name for t in response.templates]
    book_info = response.context["book_info"]
    assert book_info["book"] == book
    assert book_info["user"] == profile
