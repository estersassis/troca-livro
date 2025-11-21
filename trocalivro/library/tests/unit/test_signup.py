import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_signup_successful(client):
    url = reverse("signup")

    data = {
        "username": "novousuario",
        "firstname": "João",
        "lastname": "Silva",
        "email": "joao@example.com",
        "phone_number": "11999999999",
        "address": "Rua das Flores, 123",
        "password1": "SenhaForte123",
        "password2": "SenhaForte123",
    }

    response = client.post(url, data)

    assert response.status_code == 302
    assert response.url == "/"

    assert User.objects.filter(username="novousuario").exists()
    user = User.objects.get(username="novousuario")

    assert user.profile.address == "Rua das Flores, 123"
    assert user.profile.phone_number == "11999999999"
    assert user.profile.firstname == "João"


@pytest.mark.django_db
def test_signup_password_mismatch(client):
    url = reverse("signup")
    data = {
        "username": "badpassuser",
        "firstname": "Jane",
        "lastname": "Doe",
        "email": "jane@example.com",
        "phone_number": "987654321",
        "address": "No Way",
        "password1": "SenhaA",
        "password2": "SenhaB",
    }

    response = client.post(url, data)

    assert response.status_code == 200

    assert not User.objects.filter(username="badpassuser").exists()

    form = response.context["form"]
    assert not form.is_valid()
    assert len(form.errors) > 0


@pytest.mark.django_db
def test_signup_view_get(client):
    url = reverse("signup")
    response = client.get(url)

    assert response.status_code == 200
    assert "registration/signup.html" in [t.name for t in response.templates]
    assert "form" in response.context


@pytest.mark.django_db
def test_signup_duplicate_username(client):
    User.objects.create_user(username="existing_user", password="password123")

    url = reverse("signup")
    data = {
        "username": "existing_user",
        "firstname": "New",
        "lastname": "Person",
        "email": "new@example.com",
        "password1": "NewPass123",
        "password2": "NewPass123",
    }

    response = client.post(url, data)

    assert response.status_code == 200
    form = response.context["form"]
    assert not form.is_valid()
    assert "username" in form.errors


@pytest.mark.django_db
def test_signup_invalid_email_format(client):
    url = reverse("signup")
    data = {
        "username": "bad_email_user",
        "firstname": "Test",
        "lastname": "User",
        "email": "not-an-email",
        "password1": "Pass12345",
        "password2": "Pass12345",
    }

    response = client.post(url, data)

    assert response.status_code == 200
    form = response.context["form"]
    assert "email" in form.errors
