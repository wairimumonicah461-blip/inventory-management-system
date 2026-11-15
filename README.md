# Inventory Management System

A small Flask REST API for managing a retail company's inventory, with a command-line interface (CLI) and unit tests. Product details can be fetched from the [OpenFoodFacts API](https://world.openfoodfacts.org/data) by barcode or name, and imported straight into the inventory.

## Features

- Add, view, edit and delete inventory items (CRUD)
- Look up products on OpenFoodFacts by barcode or by name
- Import an OpenFoodFacts product into the inventory in one step
- Helper routes: search the inventory by name, list low-stock items
- Menu-based CLI that talks to the API
- Automated tests (pytest) that use mocks, so no internet is needed to run them

## Project Structure

```
app.py          Flask API (routes + OpenFoodFacts calls)
cli.py          Command-line interface
test_app.py     Tests for the API
test_cli.py     Tests for the CLI
requirements.txt
```

## Setup

1. Clone the repo and open the folder.
2. (Recommended) Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Project

Open **two terminals**.

Terminal 1 - start the API:
```
python app.py
```
The API runs at `http://127.0.0.1:5000`.

Terminal 2 - start the CLI:
```
python cli.py
```

Follow the menu to view, add, update and delete items, or to look up and import products from OpenFoodFacts. Good barcodes to try: `3017620422003` (Nutella) or `5449000000996` (Coca-Cola).

## API Routes

### Inventory (CRUD)

| Method | Route | What it does |
|--------|-------|--------------|
| GET | `/inventory` | List all items |
| GET | `/inventory/<id>` | Get one item |
| POST | `/inventory` | Add an item (`name` is required) |
| PATCH | `/inventory/<id>` | Update one or more fields of an item |
| DELETE | `/inventory/<id>` | Delete an item |

### Helper routes

| Method | Route | What it does |
|--------|-------|--------------|
| GET | `/inventory/low-stock?limit=5` | Items with stock at or below the limit |
| GET | `/inventory/search?name=milk` | Search our inventory by name |

### External API (OpenFoodFacts)

| Method | Route | What it does |
|--------|-------|--------------|
| GET | `/external/barcode/<barcode>` | Look up a product by barcode |
| GET | `/external/search?name=nutella` | Search products by name |
| POST | `/inventory/import/<barcode>` | Fetch a product and add it to the inventory (optional JSON body: `price`, `stock`) |

### Example requests

Add an item:
```
curl -X POST http://127.0.0.1:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"name": "Milk", "brand": "Brookside", "barcode": "111", "price": 1.5, "stock": 10}'
```

Update its stock:
```
curl -X PATCH http://127.0.0.1:5000/inventory/2 \
  -H "Content-Type: application/json" \
  -d '{"stock": 3}'
```

Import from OpenFoodFacts:
```
curl -X POST http://127.0.0.1:5000/inventory/import/3017620422003 \
  -H "Content-Type: application/json" \
  -d '{"price": 5.99, "stock": 12}'
```

### Item format

```json
{
  "id": 1,
  "name": "Milk",
  "brand": "Brookside",
  "barcode": "111",
  "price": 1.5,
  "stock": 10
}
```

### Error codes

- `400` - missing or bad data
- `404` - item or product not found
- `502` - OpenFoodFacts could not be reached

## Running the Tests

```
python -m pytest -v
```

The tests cover every route (success and error cases), the OpenFoodFacts integration (with mocked responses), and every CLI action.

## Design Notes

- **Storage:** items are kept in a Python list in memory, so data resets when the API restarts. This keeps the project simple; a database such as SQLite could replace the list later.
- **External API:** OpenFoodFacts needs no API key, but it asks for a `User-Agent` header, which `app.py` sends.
- **CLI flow:** the CLI never touches the data directly; it only sends requests to the API.

## Git Workflow

The project was committed to `main`. A new feature (delete confirmation in the CLI) was then built on its own branch (`feature/delete-confirmation`), merged through pull request #1, and the branch was deleted.
