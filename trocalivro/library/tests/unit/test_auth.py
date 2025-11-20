import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client

@pytest.mark.django_db
def test_login_successful(client):
    user = User.objects.create_user(username='usuario_teste', password='senha')
    url = reverse('login')
    
    response = client.post(url, {'username': 'usuario_teste', 'password': 'senha'})
    
    assert response.status_code == 302
    assert '_auth_user_id' in client.session  

@pytest.mark.django_db
def test_login_invalid_credentials(client):
    User.objects.create_user(username='usuario_teste', password='senha')
    url = reverse('login')
    
    response = client.post(url, {'username': 'usuario_teste', 'password': 'senha_errada'})
    
    assert response.status_code == 200 
    assert '_auth_user_id' not in client.session

@pytest.mark.django_db
def test_login_invalid_user(client):
    url = reverse('login')
    response = client.post(url, {'username': 'fantasma', 'password': '123'})
    
    assert response.status_code == 200
    assert '_auth_user_id' not in client.session