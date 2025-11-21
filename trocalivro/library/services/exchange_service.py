from django.db import transaction
from library.models import Book, BookExchange, StatusBook


class BookExchangeError(Exception):
    """Exceção de domínio para erros de troca de livro."""

    pass


def validate_exchange_request(book: Book, requester_profile):
    if book.owner == requester_profile:
        raise BookExchangeError("Você não pode solicitar a troca do seu próprio livro.")
    if BookExchange.objects.filter(
        book=book, requester=requester_profile, status=StatusBook.IN_EXCHANGE.value
    ).exists():
        raise BookExchangeError(
            "Você já tem uma solicitação de troca pendente para este livro."
        )
    if book.status != StatusBook.AVAILABLE.value:
        raise BookExchangeError("O livro não está disponível para troca.")


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


def get_sent_requests(requester_profile):
    """Lista solicitações enviadas pelo usuário."""
    return (
        BookExchange.objects.filter(requester=requester_profile)
        .select_related("book", "owner")
        .order_by("-id")
    )


def get_received_requests(owner_profile):
    """Lista solicitações recebidas pelo dono do livro."""
    return (
        BookExchange.objects.filter(owner=owner_profile)
        .select_related("book", "requester")
        .order_by("-id")
    )


@transaction.atomic
def respond_to_exchange_request(exchange_id: int, owner_profile, action: str, message: str = ""):
    try:
        exchange = BookExchange.objects.select_for_update().select_related("book").get(id=exchange_id)
    except BookExchange.DoesNotExist:
        raise BookExchangeError("Solicitação não encontrada.")

    if exchange.owner != owner_profile:
        raise BookExchangeError("Somente o dono do livro pode responder a solicitação.")

    if exchange.status != StatusBook.IN_EXCHANGE.value:
        raise BookExchangeError("A solicitação já foi respondida.")

    if action not in ("accept", "reject"):
        raise BookExchangeError("Ação inválida.")

    if action == "accept":
        exchange.status = StatusBook.UNAVAILABLE.value
        exchange.book.status = StatusBook.UNAVAILABLE.value
    else:
        exchange.status = StatusBook.AVAILABLE.value
        exchange.book.status = StatusBook.AVAILABLE.value

    exchange.message = message or ""
    exchange.book.save()
    exchange.save()

    return exchange
