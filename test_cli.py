"""Tests for the CLI. We fake the keyboard input and the API responses."""

from unittest.mock import patch, MagicMock

import requests

import cli


def fake_response(status_code, json_data):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    return response


ITEM = {"id": 1, "name": "Milk", "brand": "Brookside", "barcode": "111", "price": 1.5, "stock": 10}


@patch("cli.requests.request")
def test_view_all(mock_request, capsys):
    mock_request.return_value = fake_response(200, [ITEM])
    cli.view_all()
    assert "Milk" in capsys.readouterr().out


@patch("cli.requests.request")
def test_view_all_empty(mock_request, capsys):
    mock_request.return_value = fake_response(200, [])
    cli.view_all()
    assert "empty" in capsys.readouterr().out


@patch("builtins.input", return_value="1")
@patch("cli.requests.request")
def test_view_one(mock_request, mock_input, capsys):
    mock_request.return_value = fake_response(200, ITEM)
    cli.view_one()
    assert "Milk" in capsys.readouterr().out


@patch("builtins.input", return_value="99")
@patch("cli.requests.request")
def test_view_one_not_found(mock_request, mock_input, capsys):
    mock_request.return_value = fake_response(404, {"error": "Item not found"})
    cli.view_one()
    assert "Item not found" in capsys.readouterr().out


@patch("builtins.input", side_effect=["Milk", "Brookside", "111", "1.5", "10"])
@patch("cli.requests.request")
def test_add_item(mock_request, mock_input, capsys):
    mock_request.return_value = fake_response(201, ITEM)
    cli.add_item()
    assert "Item added" in capsys.readouterr().out
    # Check the CLI sent the right data to the API
    sent = mock_request.call_args.kwargs["json"]
    assert sent["price"] == 1.5
    assert sent["stock"] == 10


@patch("builtins.input", side_effect=["1", "stock", "3"])
@patch("cli.requests.request")
def test_update_item(mock_request, mock_input, capsys):
    mock_request.return_value = fake_response(200, ITEM)
    cli.update_item()
    assert "Item updated" in capsys.readouterr().out
    assert mock_request.call_args.kwargs["json"] == {"stock": 3}


@patch("builtins.input", side_effect=["1", "y"])
@patch("cli.requests.request")
def test_delete_item(mock_request, mock_input, capsys):
    mock_request.return_value = fake_response(200, {"message": "Item deleted"})
    cli.delete_item()
    assert "Item deleted" in capsys.readouterr().out


@patch("builtins.input", return_value="123")
@patch("cli.requests.request")
def test_lookup_barcode(mock_request, mock_input, capsys):
    mock_request.return_value = fake_response(200, {"name": "Nutella", "brand": "Ferrero"})
    cli.lookup_barcode()
    assert "Nutella" in capsys.readouterr().out


@patch("builtins.input", return_value="nutella")
@patch("cli.requests.request")
def test_search_by_name(mock_request, mock_input, capsys):
    mock_request.return_value = fake_response(
        200, [{"name": "Nutella", "brand": "Ferrero", "barcode": "301"}]
    )
    cli.search_by_name()
    assert "301" in capsys.readouterr().out


@patch("builtins.input", side_effect=["123", "5", "12"])
@patch("cli.requests.request")
def test_import_product(mock_request, mock_input, capsys):
    mock_request.return_value = fake_response(201, ITEM)
    cli.import_product()
    assert "imported" in capsys.readouterr().out


@patch("builtins.input", return_value="")
@patch("cli.requests.request")
def test_low_stock_default_limit(mock_request, mock_input, capsys):
    mock_request.return_value = fake_response(200, [])
    cli.low_stock()
    assert "No low stock" in capsys.readouterr().out


@patch("cli.requests.request")
def test_api_down_message(mock_request, capsys):
    mock_request.side_effect = requests.RequestException()
    cli.view_all()
    assert "could not reach the API" in capsys.readouterr().out


@patch("builtins.input", side_effect=["0"])
def test_menu_quit(mock_input, capsys):
    cli.main()
    assert "Goodbye" in capsys.readouterr().out


@patch("builtins.input", side_effect=["x", "0"])
def test_menu_invalid_choice(mock_input, capsys):
    cli.main()
    assert "Invalid choice" in capsys.readouterr().out
