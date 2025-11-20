import pytest

# Esse teste serve só para o CI não quebrar enquanto
# não criamos os testes reais de Selenium.
@pytest.mark.selenium
def test_placeholder():
    assert True