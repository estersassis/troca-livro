import pytest
from django.core.exceptions import PermissionDenied
from library.services.exchange_service import create_exchange_request, BookExchangeError
from library.models import StatusBook

@pytest.mark.django_db
def test_create_exchange_success(book_factory, profile_factory):
    owner_profile = profile_factory()
    requester_profile = profile_factory()
    book = book_factory(owner=owner_profile, status=StatusBook.AVAILABLE)

    exchange = create_exchange_request(book_id=book.id, requester_profile=requester_profile)

    assert exchange.book == book
    assert exchange.requester == requester_profile
    assert exchange.status == 'PENDING'
    book.refresh_from_db()
    assert book.status == StatusBook.PENDING_EXCHANGE

@pytest.mark.django_db
def test_cannot_request_own_book(book_factory, profile_factory):
    owner = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE)

    with pytest.raises(PermissionDenied):
        create_exchange_request(book_id=book.id, requester_profile=owner)

@pytest.mark.django_db
def test_cannot_request_unavailable_book(book_factory, profile_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.IN_EXCHANGE)

    with pytest.raises(BookExchangeError):
        create_exchange_request(book_id=book.id, requester_profile=requester)

@pytest.mark.django_db
def test_duplicate_request_not_allowed(book_factory, profile_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE)

    create_exchange_request(book_id=book.id, requester_profile=requester)

    with pytest.raises(BookExchangeError):
        create_exchange_request(book_id=book.id, requester_profile=requester)