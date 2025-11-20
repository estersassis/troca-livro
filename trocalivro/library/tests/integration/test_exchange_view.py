import pytest
from django.urls import reverse
from library.models import BookExchange, StatusBook


@pytest.mark.django_db
def test_request_exchange_view_success(
    client, user_factory, book_factory, profile_factory
):
    user = user_factory()
    profile = profile_factory(user=user)

    owner = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)

    client.force_login(user)

    url = reverse("book-request", args=[book.id])
    response = client.post(url)

    assert response.status_code == 302  # Redirect
    assert response.url == reverse("send-books")

    assert BookExchange.objects.count() == 1
    assert BookExchange.objects.first().status == StatusBook.IN_EXCHANGE.value
    book.refresh_from_db()
    assert book.status == StatusBook.IN_EXCHANGE.value


@pytest.mark.django_db
def test_request_exchange_view_cannot_request_own_book(
    client, user_factory, book_factory, profile_factory
):
    user = user_factory()
    profile = profile_factory(user=user)

    book = book_factory(owner=profile, status=StatusBook.AVAILABLE.value)

    client.force_login(user)

    url = reverse("book-request", args=[book.id])
    response = client.post(url)

    # assert warning message in response
    assert response.status_code == 302  # Redirect
    assert response.url == reverse("index")

    assert BookExchange.objects.count() == 0


@pytest.mark.django_db
def test_request_exchange_view_cannot_request_unavailable_book(
    client, user_factory, book_factory, profile_factory
):
    user = user_factory()
    profile = profile_factory(user=user)

    owner = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.IN_EXCHANGE.value)

    client.force_login(user)

    url = reverse("book-request", args=[book.id])
    response = client.post(url)

    # assert warning message in response
    assert response.status_code == 302  # Redirect
    assert response.url == reverse("index")

    assert BookExchange.objects.count() == 0


@pytest.mark.django_db
def test_request_exchange_view_duplicate_request_not_allowed(
    client, user_factory, book_factory, profile_factory
):
    user = user_factory()
    profile = profile_factory(user=user)

    owner = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)

    client.force_login(user)

    url = reverse("book-request", args=[book.id])
    response1 = client.post(url)
    response2 = client.post(url)

    # assert warning message in response
    assert response2.status_code == 302  # Redirect
    assert response2.url == reverse("index")

    assert BookExchange.objects.count() == 1


@pytest.mark.django_db
def test_request_exchange_view_request_nonexistent_book(
    client, user_factory, profile_factory
):
    user = user_factory()
    profile = profile_factory(user=user)

    client.force_login(user)

    url = reverse("book-request", args=[9999])  # Non-existent book ID
    response = client.post(url)

    # assert warning message in response
    assert response.status_code == 302  # Redirect
    assert response.url == reverse("index")

    assert BookExchange.objects.count() == 0
