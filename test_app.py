"""Tests for the Flask API (CRUD, helper routes, external API with mocks)."""

from unittest.mock import patch, MagicMock

import pytest
import requests

import app as app_module


@pytest.fixture(autouse=True)
def reset_data():
    """Give every test a fresh inventory."""
    app_module.inventory.clear()
    app_module.inventory.append(
        {"id": 1, "name": "Milk", "brand": "Brookside", "barcode": "111", "price": 1.5, "stock": 10}
    )
    app_module.next_id = 2


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def fake_response(json_data):
    response = MagicMock()
    response.json.return_value = json_data
    return response


# ---------- READ ----------

def test_get_all_items(client):
    response = client.get("/inventory")
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_get_one_item(client):
    response = client.get("/inventory/1")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Milk"


def test_get_item_not_found(client):
    response = client.get("/inventory/99")
    assert response.status_code == 404


# ---------- CREATE ----------

def test_add_item(client):
    response = client.post("/inventory", json={"name": "Bread", "price": 2, "stock": 5})
    assert response.status_code == 201
    assert response.get_json()["id"] == 2
    assert len(app_module.inventory) == 2


def test_add_item_without_name(client):
    response = client.post("/inventory", json={"price": 2})
    assert response.status_code == 400


# ---------- UPDATE ----------

def test_update_item(client):
    response = client.patch("/inventory/1", json={"stock": 3})
    assert response.status_code == 200
    assert response.get_json()["stock"] == 3


def test_update_cannot_change_id(client):
    client.patch("/inventory/1", json={"id": 50})
    assert app_module.inventory[0]["id"] == 1


def test_update_item_not_found(client):
    response = client.patch("/inventory/99", json={"stock": 3})
    assert response.status_code == 404


def test_update_with_no_data(client):
    response = client.patch("/inventory/1", json={})
    assert response.status_code == 400


# ---------- DELETE ----------

def test_delete_item(client):
    response = client.delete("/inventory/1")
    assert response.status_code == 200
    assert len(app_module.inventory) == 0


def test_delete_item_not_found(client):
    response = client.delete("/inventory/99")
    assert response.status_code == 404


# ---------- Helper routes ----------

def test_low_stock(client):
    client.post("/inventory", json={"name": "Eggs", "stock": 2})
    response = client.get("/inventory/low-stock?limit=5")
    names = [item["name"] for item in response.get_json()]
    assert names == ["Eggs"]


def test_search_inventory(client):
    response = client.get("/inventory/search?name=mil")
    assert len(response.get_json()) == 1
    response = client.get("/inventory/search?name=zzz")
    assert response.get_json() == []


# ---------- External API (mocked, no real internet needed) ----------

BARCODE_DATA = {
    "status": 1,
    "product": {"product_name": "Nutella", "brands": "Ferrero", "ingredients_text": "Sugar"},
}


@patch("app.requests.get")
def test_external_barcode_found(mock_get, client):
    mock_get.return_value = fake_response(BARCODE_DATA)
    response = client.get("/external/barcode/3017620422003")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Nutella"


@patch("app.requests.get")
def test_external_barcode_not_found(mock_get, client):
    mock_get.return_value = fake_response({"status": 0})
    response = client.get("/external/barcode/000")
    assert response.status_code == 404


@patch("app.requests.get")
def test_external_barcode_api_down(mock_get, client):
    mock_get.side_effect = requests.RequestException()
    response = client.get("/external/barcode/123")
    assert response.status_code == 502


@patch("app.requests.get")
def test_external_search(mock_get, client):
    mock_get.return_value = fake_response(
        {"products": [{"product_name": "Nutella", "brands": "Ferrero", "code": "301"}]}
    )
    response = client.get("/external/search?name=nutella")
    assert response.status_code == 200
    assert response.get_json()[0]["barcode"] == "301"


def test_external_search_needs_name(client):
    response = client.get("/external/search")
    assert response.status_code == 400


@patch("app.requests.get")
def test_import_adds_to_inventory(mock_get, client):
    mock_get.return_value = fake_response(BARCODE_DATA)
    response = client.post("/inventory/import/3017620422003", json={"price": 5, "stock": 12})
    assert response.status_code == 201
    assert len(app_module.inventory) == 2
    assert app_module.inventory[-1]["name"] == "Nutella"
    assert app_module.inventory[-1]["stock"] == 12


@patch("app.requests.get")
def test_import_not_found_adds_nothing(mock_get, client):
    mock_get.return_value = fake_response({"status": 0})
    response = client.post("/inventory/import/000")
    assert response.status_code == 404
    assert len(app_module.inventory) == 1
