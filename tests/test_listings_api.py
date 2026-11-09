from tests.conftest import ADMIN

def test_empty_database_returns_no_listings(client):
    response = client.get("api/listings")
    assert response.status_code == 200
    assert response.json() == {"total": 0, "limit": 20, "offset": 0, "items": []}


def test_create_needs_api_key(client):
    body = {"sector": "pharma", "title": "Graduate Chemist",
            "url": "https://example.com/a"}
    assert client.post("/api/listings", json=body).status_code == 401
    assert client.post("/api/listings", json=body, headers={"X-API-KEY": "wrong"}).status_code == 401

def test_create_then_read_back(client, make_listing):
    created = make_listing(title="Graduate Chemist")
    response = client.get(f"/api/listings/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Graduate Chemist"
    assert response.json()["source"] == "manual"

def test_bad_input_is_rejected(client):
    body = {"sector": "finance", "title": "x", "url": "not-a-url"}
    response = client.post("/api/listings", json=body, headers=ADMIN)
    assert response.status_code == 422

def test_filter_by_sector(client, make_listing):
    make_listing(sector="pharma", title="Graduate Chemist")
    make_listing(sector="psychology", title="Assistant Psychologist")
    response = client.get("api/listings", params={"sector": "psychology"})
    titles = [item["title"] for item in response.json()["items"]]
    assert titles == ["Assistant Psychologist"]

def test_search_matches_title_and_company(client, make_listing):
    make_listing(title="Graduate Chemist", company="GSK")
    make_listing(title="Lab Analyst", company="Pfizer")
    assert client.get("/api/listings", params={"q": "chem"}).json()["total"] == 1
    assert client.get("api/listings", params={"q": "pfizer"}).json()["total"] == 1

def test_pagination(client, make_listing):
    for n in range(5):
        make_listing(title=f"Graduate Role {n}")
    page = client.get("/api/listings", params={"limit": 2, "offset": 2}).json()
    assert page["total"] == 5
    assert len(page["items"]) == 2

def test_missing_listing_returns_404(client):
    assert client.get("/api/listings/999").status_code == 404

def test_delete(client, make_listing):
    created = make_listing()
    assert client.delete(f"/api/listings/{created['id']}").status_code == 401
    assert client.delete(f"/api/listings/{created['id']}", headers=ADMIN).status_code == 204
    assert client.get(f"/api/listings/{created['id']}").status_code == 404

def test_stats_counts_by_sector(client, make_listing):
    make_listing(sector="pharma")
    make_listing(sector="pharma")
    make_listing(sector="psychology")
    stats = client.get("/api/stats").json()
    assert stats["total"] == 3
    assert stats["by_sector"] == {"pharma": 2, "psychology": 1}
    assert stats["last_fetch_status"] is None




