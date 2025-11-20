from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone

from library.models import Book, BookExchange, StatusBook

class BookExchangeError(Exception):
    """Exceção de domínio para erros de troca de livro."""
    pass

def validate_exchange_request(book: Book, requester_profile):
    ...
 
@transaction.atomic
def create_exchange_request(book_id: int, requester_profile):
    ...