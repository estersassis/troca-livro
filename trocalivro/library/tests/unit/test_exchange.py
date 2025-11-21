import pytest
from library.services.exchange_service import (
    BookExchangeError,
    create_exchange_request,
    get_received_requests,
    get_sent_requests,
    respond_to_exchange_request,
)
from library.models import StatusBook


@pytest.mark.django_db
def test_create_exchange_success(book_factory, profile_factory):
    owner_profile = profile_factory()
    requester_profile = profile_factory()
    book = book_factory(owner=owner_profile, status=StatusBook.AVAILABLE.value)

    exchange = create_exchange_request(
        book_id=book.id, requester_profile=requester_profile
    )

    assert exchange.book == book
    assert exchange.requester == requester_profile
    assert exchange.status == StatusBook.IN_EXCHANGE.value
    book.refresh_from_db()
    assert book.status == StatusBook.IN_EXCHANGE.value


@pytest.mark.django_db
def test_cannot_request_own_book(book_factory, profile_factory):
    owner = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)

    with pytest.raises(BookExchangeError) as excinfo:
        create_exchange_request(book_id=book.id, requester_profile=owner)
    assert "Você não pode solicitar a troca do seu próprio livro." in str(excinfo.value)


@pytest.mark.django_db
def test_cannot_request_unavailable_book(book_factory, profile_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.IN_EXCHANGE.value)

    with pytest.raises(BookExchangeError) as excinfo:
        create_exchange_request(book_id=book.id, requester_profile=requester)
    assert "O livro não está disponível para troca." in str(excinfo.value)


@pytest.mark.django_db
def test_duplicate_request_not_allowed(book_factory, profile_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)

    create_exchange_request(book_id=book.id, requester_profile=requester)

    with pytest.raises(BookExchangeError) as excinfo:
        create_exchange_request(book_id=book.id, requester_profile=requester)
    assert "Você já tem uma solicitação de troca pendente para este livro." in str(
        excinfo.value
    )


@pytest.mark.django_db
def test_request_nonexistent_book(profile_factory):
    requester = profile_factory()

    with pytest.raises(BookExchangeError) as excinfo:
        create_exchange_request(book_id=9999, requester_profile=requester)
    assert "Livro não encontrado." in str(excinfo.value)


@pytest.mark.django_db
def test_get_sent_requests_returns_only_user_requests(profile_factory, book_factory):
    owner = profile_factory()
    requester = profile_factory()
    other_requester = profile_factory()

    book_requested = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)
    book_not_requested = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)

    sent_exchange = create_exchange_request(
        book_id=book_requested.id, requester_profile=requester
    )
    create_exchange_request(
        book_id=book_not_requested.id, requester_profile=other_requester
    )

    sent_requests = list(get_sent_requests(requester))

    assert sent_requests == [sent_exchange]


@pytest.mark.django_db
def test_get_received_requests_returns_only_owner_requests(
    profile_factory, book_factory
):
    owner = profile_factory()
    requester = profile_factory()
    other_owner = profile_factory()

    book_owned = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)
    other_book = book_factory(owner=other_owner, status=StatusBook.AVAILABLE.value)

    exchange = create_exchange_request(
        book_id=book_owned.id, requester_profile=requester
    )
    create_exchange_request(book_id=other_book.id, requester_profile=requester)

    received_requests = list(get_received_requests(owner))

    assert received_requests == [exchange]


@pytest.mark.django_db
def test_respond_to_exchange_accepts_and_updates_status(profile_factory, book_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)
    exchange = create_exchange_request(book_id=book.id, requester_profile=requester)

    respond_to_exchange_request(
        exchange_id=exchange.id,
        owner_profile=owner,
        action="accept",
        message="Vamos trocar!",
    )

    exchange.refresh_from_db()
    book.refresh_from_db()
    assert exchange.status == StatusBook.UNAVAILABLE.value
    assert exchange.message == "Vamos trocar!"
    assert book.status == StatusBook.UNAVAILABLE.value


@pytest.mark.django_db
def test_respond_to_exchange_reject_resets_book(profile_factory, book_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)
    exchange = create_exchange_request(book_id=book.id, requester_profile=requester)

    respond_to_exchange_request(
        exchange_id=exchange.id,
        owner_profile=owner,
        action="reject",
        message="Não estou interessado.",
    )

    exchange.refresh_from_db()
    book.refresh_from_db()
    assert exchange.status == StatusBook.AVAILABLE.value
    assert exchange.message == "Não estou interessado."
    assert book.status == StatusBook.AVAILABLE.value


@pytest.mark.django_db
def test_respond_to_exchange_only_owner_can_reply(profile_factory, book_factory):
    owner = profile_factory()
    requester = profile_factory()
    outsider = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)
    exchange = create_exchange_request(book_id=book.id, requester_profile=requester)

    with pytest.raises(BookExchangeError) as excinfo:
        respond_to_exchange_request(
            exchange_id=exchange.id,
            owner_profile=outsider,
            action="reject",
        )

    assert "Somente o dono do livro pode responder a solicitação." in str(excinfo.value)


@pytest.mark.django_db
def test_cannot_respond_twice(profile_factory, book_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)
    exchange = create_exchange_request(book_id=book.id, requester_profile=requester)

    respond_to_exchange_request(
        exchange_id=exchange.id,
        owner_profile=owner,
        action="accept",
    )

    with pytest.raises(BookExchangeError) as excinfo:
        respond_to_exchange_request(
            exchange_id=exchange.id,
            owner_profile=owner,
            action="reject",
        )

    assert "A solicitação já foi respondida." in str(excinfo.value)


@pytest.mark.django_db
def test_cannot_respond_invalid_action(profile_factory, book_factory):
    owner = profile_factory()
    requester = profile_factory()
    book = book_factory(owner=owner, status=StatusBook.AVAILABLE.value)
    exchange = create_exchange_request(book_id=book.id, requester_profile=requester)

    with pytest.raises(BookExchangeError) as excinfo:
        respond_to_exchange_request(
            exchange_id=exchange.id,
            owner_profile=owner,
            action="invalid",
        )

    assert "Ação inválida." in str(excinfo.value)


@pytest.mark.django_db
def test_respond_to_nonexistent_exchange(profile_factory):
    owner = profile_factory()

    with pytest.raises(BookExchangeError) as excinfo:
        respond_to_exchange_request(
            exchange_id=9999,
            owner_profile=owner,
            action="accept",
        )

    assert "Solicitação não encontrada." in str(excinfo.value)
