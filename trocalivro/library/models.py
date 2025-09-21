from django.db import models
from django.utils import timezone
from django.urls import reverse 
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from enum import Enum

# Modificado valores do Enum para maiusculo para casar com as informações no frontend
class StatusBook(Enum):
  AVAILABLE = 'AVAILABLE'
  IN_EXCHANGE = 'IN EXCHANGE'
  UNAVAILABLE = 'UNAVAILABLE'


class Profile(models.Model):
  user = models.OneToOneField(User, related_name='profile', on_delete = models.CASCADE, null=True)
  firstname = models.CharField(max_length = 255)
  lastname = models.CharField(max_length = 255)
  email = models.EmailField(default = "", null = True)
  phone_number = models.CharField(max_length = 255,default = "")
  reputation = models.IntegerField(default = 5) 
  address = models.TextField(default = "")

  @receiver(post_save, sender=User)
  def create_user_profile(sender, instance, created, **kwargs):
      if created:
          Profile.objects.create(user=instance)

  @receiver(post_save, sender=User)
  def save_user_profile(sender, instance, **kwargs):
      instance.profile.save()
    

class Book(models.Model):
  title = models.CharField(max_length = 255)
  description = models.TextField()
  genre = models.CharField(max_length=200, default = "", null = True)
  image = models.ImageField(upload_to='library/static/images/', blank=True, null=True)
  status = models.CharField(max_length = 20, choices = [(tag.name, tag.value) for tag in StatusBook])
  # Adicionado campo de autor no banco de dados.
  author = models.CharField(max_length=255, null=True)
  created_at = models.DateField(default=timezone.now)
  owner = models.ForeignKey(Profile, on_delete = models.CASCADE)

  def get_absolute_url(self):
    return reverse('book-detail', args=[str(self.id)])


# Tabela que irá armazenar as informações das trocas entre os usuários.
class BookExchange(models.Model):
    # Basicamente uma tabela com chaves estrangeiras que será usada para consultar as interações entre os usuários
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    requester = models.ForeignKey(Profile, related_name='requested_books', on_delete=models.CASCADE)
    owner = models.ForeignKey(Profile, related_name='owned_books', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[(tag.name, tag.value) for tag in StatusBook])
    

    def save(self, *args, **kwargs):
        # Atualiza o status do livro com base no status da troca
        if self.status == StatusBook.IN_EXCHANGE.value:
            self.book.status = StatusBook.IN_EXCHANGE.value
            self.book.save()
        elif self.status == StatusBook.AVAILABLE.value:
            self.book.status = StatusBook.AVAILABLE.value
            self.book.save()
        super().save(*args, **kwargs)