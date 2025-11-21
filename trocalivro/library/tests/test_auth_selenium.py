import uuid

import pytest
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(scope="session")
def selenium_driver():
    """Provide a headless Chrome driver or skip if it cannot be started."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as exc:  # pragma: no cover - defensive branch
        pytest.skip(f"Chromedriver indisponível: {exc}")
    else:
        yield driver
        driver.quit()

@pytest.fixture(autouse=True)
def _reset_driver_state(selenium_driver):
    selenium_driver.delete_all_cookies()
    yield


def _wait_for_text(driver, css_selector, text):
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element((By.CSS_SELECTOR, css_selector), text)
    )


def _login_user(driver, live_server, username, password):
    login_url = f"{live_server.url}/library/accounts/login/"
    driver.get(login_url)
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button.submit-button").click()
    WebDriverWait(driver, 10).until(EC.url_contains("/library/"))


@pytest.mark.selenium
@pytest.mark.django_db(transaction=True)
def test_signup_shows_validation_errors(live_server, selenium_driver):
    signup_url = f"{live_server.url}/library/signup/"
    selenium_driver.get(signup_url)

    selenium_driver.find_element(By.NAME, "username").send_keys("invalid_user")
    selenium_driver.find_element(By.NAME, "firstname").send_keys("Nome")
    selenium_driver.find_element(By.NAME, "lastname").send_keys("Sobrenome")
    selenium_driver.find_element(By.NAME, "email").send_keys("email@example.com")
    selenium_driver.find_element(By.NAME, "phone_number").send_keys("123456789")
    selenium_driver.find_element(By.NAME, "address").send_keys("Rua sem numero")
    selenium_driver.find_element(By.NAME, "password1").send_keys("SenhaValida123")
    selenium_driver.find_element(By.NAME, "password2").send_keys("SenhaDiferente456")
    selenium_driver.find_element(By.CSS_SELECTOR, "input.submit-button").click()

    _wait_for_text(selenium_driver, ".alert.error", "Por favor, corrija os erros abaixo.")
    alerts = selenium_driver.find_elements(By.CSS_SELECTOR, ".alert.error")
    assert alerts, "Mensagem de erro não exibida"


@pytest.mark.selenium
@pytest.mark.django_db(transaction=True)
def test_successful_signup_and_login_flow(live_server, selenium_driver):
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "StrongPass123!"
    signup_url = f"{live_server.url}/library/signup/"

    selenium_driver.get(signup_url)
    selenium_driver.find_element(By.NAME, "username").send_keys(username)
    selenium_driver.find_element(By.NAME, "firstname").send_keys("Test")
    selenium_driver.find_element(By.NAME, "lastname").send_keys("User")
    selenium_driver.find_element(By.NAME, "email").send_keys("test@example.com")
    selenium_driver.find_element(By.NAME, "phone_number").send_keys("123456789")
    selenium_driver.find_element(By.NAME, "address").send_keys("Rua Selenium, 123")
    selenium_driver.find_element(By.NAME, "password1").send_keys(password)
    selenium_driver.find_element(By.NAME, "password2").send_keys(password)
    selenium_driver.find_element(By.CSS_SELECTOR, "input.submit-button").click()

    _wait_for_text(
        selenium_driver,
        ".alert.success",
        "Conta criada com sucesso! Faça login para continuar.",
    )
    assert User.objects.filter(username=username).exists()

    login_url = f"{live_server.url}/library/accounts/login/"
    selenium_driver.get(login_url)
    selenium_driver.find_element(By.NAME, "username").send_keys(username)
    selenium_driver.find_element(By.NAME, "password").send_keys(password)
    selenium_driver.find_element(By.CSS_SELECTOR, "button.submit-button").click()

    WebDriverWait(selenium_driver, 10).until(
        EC.url_contains("/library/")
    )
    logout_forms = selenium_driver.find_elements(By.CSS_SELECTOR, "form[action*='logout']")
    assert logout_forms, "Usuário não autenticado após login"


@pytest.mark.selenium
@pytest.mark.django_db(transaction=True)
def test_profile_requires_auth_redirects_to_login(live_server, selenium_driver):
    profile_url = f"{live_server.url}/library/profile/"
    selenium_driver.get(profile_url)
    WebDriverWait(selenium_driver, 10).until(EC.url_contains("/accounts/login/"))
    assert "next=/library/profile/" in selenium_driver.current_url


@pytest.mark.selenium
@pytest.mark.django_db(transaction=True)
def test_login_with_invalid_credentials_shows_error(live_server, selenium_driver):
    User.objects.create_user(username="loginuser", password="CorrectPass123")
    login_url = f"{live_server.url}/library/accounts/login/"

    selenium_driver.get(login_url)
    selenium_driver.find_element(By.NAME, "username").send_keys("loginuser")
    selenium_driver.find_element(By.NAME, "password").send_keys("WrongPass123")
    selenium_driver.find_element(By.CSS_SELECTOR, "button.submit-button").click()

    _wait_for_text(
        selenium_driver,
        "body",
        "Your username and password didn't match. Please try again.",
    )


@pytest.mark.selenium
@pytest.mark.django_db(transaction=True)
def test_authenticated_user_can_add_book(live_server, selenium_driver):
    username = f"booker_{uuid.uuid4().hex[:6]}"
    password = "BookPass123!"
    user = User.objects.create_user(username=username, password=password, first_name="Book", last_name="User")

    _login_user(selenium_driver, live_server, username, password)

    add_book_url = f"{live_server.url}/library/book/"
    selenium_driver.get(add_book_url)

    WebDriverWait(selenium_driver, 10).until(
        EC.presence_of_element_located((By.NAME, "title"))
    )
    selenium_driver.find_element(By.NAME, "title").send_keys("Selenium Adventures")
    selenium_driver.find_element(By.NAME, "description").send_keys("Testando cadastro de livros via Selenium.")
    selenium_driver.find_element(By.NAME, "genre").send_keys("Teste")
    selenium_driver.find_element(By.NAME, "author").send_keys("Autor Selenium")
    selenium_driver.find_element(By.CSS_SELECTOR, "button.input-profile-btn").click()

    WebDriverWait(selenium_driver, 10).until(EC.url_contains("/library/profile"))
    _wait_for_text(selenium_driver, ".alert.success", "Livro cadastrado com sucesso.")
    assert user.profile.book_set.filter(title="Selenium Adventures").exists()
