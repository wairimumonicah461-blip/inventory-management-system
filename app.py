"""Inventory Management System - Flask REST API.

Data is stored in a simple Python list (our "database array").
Product details can be fetched from the OpenFoodFacts API.
"""

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

OFF_BASE_URL = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "InventoryManagementLab/1.0 (student project)"}

# Our "database": a list of dictionaries
inventory = [
    {
        "id": 1,
        "name": "Sample Cereal",
        "brand": "Sample Brand",
        "barcode": "0000000000000",
        "price": 4.99,
        "stock": 20,
    }
]
next_id = 2


# ---------- Helper functions ----------

def find_item(item_id):
    """Return the item with this id, or None."""
    for item in inventory:
        if item["id"] == item_id:
            return item
    return None


def fetch_product_by_barcode(barcode):
    """Ask OpenFoodFacts for a product by barcode. Returns a dict or None."""
    url = f"{OFF_BASE_URL}/api/v0/product/{barcode}.json"
    response = requests.get(url, headers=HEADERS, timeout=10)
    data = response.json()
    if data.get("status") != 1:
        return None
    return clean_product(data["product"], barcode)


def search_products_by_name(name):
    """Search OpenFoodFacts by product name. Returns a list of dicts."""
    url = f"{OFF_BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
    }
    response = requests.get(url, params=params, headers=HEADERS, timeout=10)
    data = response.json()
    results = []
    for product in data.get("products", []):
        results.append(clean_product(product, product.get("code", "")))
    return results


def clean_product(product, barcode):
    """Keep only the fields we care about."""
    return {
        "name": product.get("product_name", "Unknown"),
        "brand": product.get("brands", "Unknown"),
        "barcode": barcode,
        "ingredients": product.get("ingredients_text", ""),
    }


# ---------- CRUD routes ----------

@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify(inventory), 200


@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def add_item():
    global next_id
    data = request.get_json(silent=True)
    if not data or "name" not in data:
        return jsonify({"error": "Name is required"}), 400

    item = {
        "id": next_id,
        "name": data["name"],
        "brand": data.get("brand", ""),
        "barcode": data.get("barcode", ""),
        "price": data.get("price", 0),
        "stock": data.get("stock", 0),
    }
    next_id += 1
    inventory.append(item)
    return jsonify(item), 201


@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Only update fields that already exist (and not the id)
    for key in data:
        if key in item and key != "id":
            item[key] = data[key]
    return jsonify(item), 200


@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    inventory.remove(item)
    return jsonify({"message": "Item deleted"}), 200


# ---------- Extra helper routes ----------

@app.route("/inventory/low-stock", methods=["GET"])
def low_stock():
    """Items with stock at or below a limit (default 5)."""
    limit = request.args.get("limit", 5, type=int)
    items = [item for item in inventory if item["stock"] <= limit]
    return jsonify(items), 200


@app.route("/inventory/search", methods=["GET"])
def search_inventory():
    """Search our own inventory by name."""
    name = request.args.get("name", "").lower()
    items = [item for item in inventory if name in item["name"].lower()]
    return jsonify(items), 200


# ---------- External API routes ----------

@app.route("/external/barcode/<barcode>", methods=["GET"])
def external_by_barcode(barcode):
    try:
        product = fetch_product_by_barcode(barcode)
    except requests.RequestException:
        return jsonify({"error": "Could not reach OpenFoodFacts"}), 502
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200


@app.route("/external/search", methods=["GET"])
def external_by_name():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Please provide a name"}), 400
    try:
        products = search_products_by_name(name)
    except requests.RequestException:
        return jsonify({"error": "Could not reach OpenFoodFacts"}), 502
    return jsonify(products), 200


@app.route("/inventory/import/<barcode>", methods=["POST"])
def import_from_external(barcode):
    """Fetch a product from OpenFoodFacts and add it to our inventory."""
    global next_id
    try:
        product = fetch_product_by_barcode(barcode)
    except requests.RequestException:
        return jsonify({"error": "Could not reach OpenFoodFacts"}), 502
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json(silent=True) or {}
    item = {
        "id": next_id,
        "name": product["name"],
        "brand": product["brand"],
        "barcode": product["barcode"],
        "price": data.get("price", 0),
        "stock": data.get("stock", 0),
    }
    next_id += 1
    inventory.append(item)
    return jsonify(item), 201


if __name__ == "__main__":
    app.run(debug=True)
