import pytest

from app.pages import format_pay

def test_home_lists_roles(client, make_listing):
    make_listing(title="Graduate Chemist", company="GSK")
    response = client.get("/")
    assert response.status_code == 200
    assert "Graduate Chemist" in response.text
    assert "1 role found" in response.text

def test_home_page_ignores_unknown_sector(client):
    assert client.get("/", params={"sector": "<script>"}).status_code == 200

@pytest.mark.parametrize(
    ("salary_min", "salary_max", "salary_type", "expected"),
    [
        (30000, 32000, "per annum", "£30,000 to £32,000 per annum"),
        (93, 120, "per day", "£93 to £120 per day"),
        (12.5, 12.5, "per hour", "£12.50 per hour"),
        (None, 30000, None, "£30,000"),
        (None, None, "per day", ""),
    ],
)
def test_format_pay(salary_min, salary_max, salary_type, expected):
    assert format_pay(salary_min, salary_max, salary_type) == expected


