import pytest
from library.services.exchange_service import create_exchange_request, BookExchangeError, PermissionDenied
from library.models import StatusBook

@pytest.mark.django_db
def test_create_exchange_success(book_factory, profile_factory):
    owner_profile = profile_factory()
    requester_profile = profile_factory()
    book = book_factory(owner=owner_profile, status=StatusBook.AVAILABLE.value)

    exchange = create_exchange_request(book_id=book.id, requester_profile=requester_profile)

    assert exchange.book == book
    assert exchange.requester == requester_profile
    assert exchange.status == StatusBook.IN_EXCHANGE.value
    book.refresh_from_db()
    assert book.status == StatusBook.IN_EXCHANGE.value

@pytest.mark.django_db
def test_cannot_request_own_book(book_factory, profile_factory):
    owner = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)

    with pytest.raises(PermissionDenied):
        create_exchange_request(book_id=book.id, requester_profile=owner)

@pytest.mark.django_db
def test_cannot_request_unavailable_book(book_factory, profile_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.IN_EXCHANGE.value)

    with pytest.raises(BookExchangeError):
        create_exchange_request(book_id=book.id, requester_profile=requester)

@pytest.mark.django_db
def test_duplicate_request_not_allowed(book_factory, profile_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)

    create_exchange_request(book_id=book.id, requester_profile=requester)

    with pytest.raises(BookExchangeError):
        create_exchange_request(book_id=book.id, requester_profile=requester)