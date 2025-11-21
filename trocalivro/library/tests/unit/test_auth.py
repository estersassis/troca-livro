import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_login_successful(client):
    User.objects.create_user(username="usuario_teste", password="senha")
    url = reverse("custom_login")

    response = client.post(url, {"username": "usuario_teste", "password": "senha"})

    assert response.status_code == 302
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_user_already_authenticated(client):
    user = User.objects.create_user(username="usuario_teste", password="senha")
    client.force_login(user)

    url = reverse("custom_login")
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse("index")


@pytest.mark.django_db
def test_login_invalid_credentials(client):
    User.objects.create_user(username="usuario_teste", password="senha")
    url = reverse("custom_login")

    response = client.post(
        url, {"username": "usuario_teste", "password": "senha_errada"}
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_login_invalid_user(client):
    url = reverse("custom_login")
    response = client.post(
        url, {"username": "usuario_fake", "password": "senha_errada"}
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_login_invalid_form_data(client):
    url = reverse("custom_login")
    data = {}

    response = client.post(url, data)

    assert response.status_code == 200
    form = response.context["form"]
    assert not form.is_valid()


@pytest.mark.django_db
def test_login_view_get(client):
    url = reverse("custom_login")
    response = client.get(url)

    assert response.status_code == 200
    assert "registration/login.html" in [t.name for t in response.templates]
    assert "form" in response.context
