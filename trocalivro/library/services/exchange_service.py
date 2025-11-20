from django.db import transaction
from library.models import Book, BookExchange, StatusBook


class BookExchangeError(Exception):
    """Exceção de domínio para erros de troca de livro."""

    pass


def validate_exchange_request(book: Book, requester_profile):
    if book.owner == requester_profile:
        raise BookExchangeError("Você não pode solicitar a troca do seu próprio livro.")
    if book.status != StatusBook.AVAILABLE.value:
        raise BookExchangeError("O livro não está disponível para troca.")
    if BookExchange.objects.filter(
        book=book, requester=requester_profile, status="PENDING"
    ).exists():
        raise BookExchangeError(
            "Você já tem uma solicitação de troca pendente para este livro."
        )


@transaction.atomic
def create_exchange_request(book_id: int, requester_profile):
    try:
        book = Book.objects.select_for_update().get(id=book_id)
    except Book.DoesNotExist:
        raise BookExchangeError("Livro não encontrado.")

    validate_exchange_request(book, requester_profile)

    exchange = BookExchange.objects.create(
        book=book,
        requester=requester_profile,
        owner=book.owner,
        status=StatusBook.IN_EXCHANGE.value,
    )

    return exchange
