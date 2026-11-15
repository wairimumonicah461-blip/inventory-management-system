"""Simple command-line interface for the Inventory API.

Start the API first (python app.py), then run: python cli.py
"""

import requests

API_URL = "http://127.0.0.1:5000"


def show_item(item):
    print(
        f"[{item['id']}] {item['name']} | brand: {item['brand']} | "
        f"barcode: {item['barcode']} | price: {item['price']} | stock: {item['stock']}"
    )


def call_api(method, path, **kwargs):
    """Send a request to the API. Returns the response or None if the API is down."""
    try:
        return requests.request(method, API_URL + path, timeout=15, **kwargs)
    except requests.RequestException:
        print("Error: could not reach the API. Is app.py running?")
        return None


def view_all():
    response = call_api("GET", "/inventory")
    if response is None:
        return
    items = response.json()
    if not items:
        print("Inventory is empty.")
    for item in items:
        show_item(item)


def view_one():
    item_id = input("Item id: ")
    response = call_api("GET", f"/inventory/{item_id}")
    if response is None:
        return
    if response.status_code == 200:
        show_item(response.json())
    else:
        print(response.json()["error"])


def add_item():
    name = input("Name: ")
    brand = input("Brand: ")
    barcode = input("Barcode: ")
    price = float(input("Price: "))
    stock = int(input("Stock: "))
    data = {"name": name, "brand": brand, "barcode": barcode, "price": price, "stock": stock}
    response = call_api("POST", "/inventory", json=data)
    if response is None:
        return
    if response.status_code == 201:
        print("Item added:")
        show_item(response.json())
    else:
        print(response.json()["error"])


def update_item():
    item_id = input("Item id to update: ")
    field = input("Field to change (name, brand, barcode, price, stock): ")
    value = input("New value: ")
    if field == "price":
        value = float(value)
    elif field == "stock":
        value = int(value)
    response = call_api("PATCH", f"/inventory/{item_id}", json={field: value})
    if response is None:
        return
    if response.status_code == 200:
        print("Item updated:")
        show_item(response.json())
    else:
        print(response.json()["error"])


def delete_item():
    item_id = input("Item id to delete: ")
    response = call_api("DELETE", f"/inventory/{item_id}")
    if response is None:
        return
    if response.status_code == 200:
        print("Item deleted.")
    else:
        print(response.json()["error"])


def lookup_barcode():
    barcode = input("Barcode: ")
    response = call_api("GET", f"/external/barcode/{barcode}")
    if response is None:
        return
    if response.status_code == 200:
        product = response.json()
        print(f"Found: {product['name']} by {product['brand']}")
    else:
        print(response.json()["error"])


def search_by_name():
    name = input("Product name: ")
    response = call_api("GET", "/external/search", params={"name": name})
    if response is None:
        return
    if response.status_code == 200:
        products = response.json()
        if not products:
            print("No products found.")
        for product in products:
            print(f"{product['name']} | {product['brand']} | barcode: {product['barcode']}")
    else:
        print(response.json()["error"])


def import_product():
    barcode = input("Barcode to import: ")
    price = float(input("Price: "))
    stock = int(input("Stock: "))
    response = call_api(
        "POST", f"/inventory/import/{barcode}", json={"price": price, "stock": stock}
    )
    if response is None:
        return
    if response.status_code == 201:
        print("Product imported into inventory:")
        show_item(response.json())
    else:
        print(response.json()["error"])


def low_stock():
    limit = input("Show items with stock at or below (default 5): ") or "5"
    response = call_api("GET", "/inventory/low-stock", params={"limit": limit})
    if response is None:
        return
    items = response.json()
    if not items:
        print("No low stock items.")
    for item in items:
        show_item(item)


MENU = """
===== Inventory Manager =====
1. View all items
2. View one item
3. Add item
4. Update item
5. Delete item
6. Look up product by barcode (OpenFoodFacts)
7. Search product by name (OpenFoodFacts)
8. Import product from OpenFoodFacts
9. Show low stock items
0. Quit
"""

ACTIONS = {
    "1": view_all,
    "2": view_one,
    "3": add_item,
    "4": update_item,
    "5": delete_item,
    "6": lookup_barcode,
    "7": search_by_name,
    "8": import_product,
    "9": low_stock,
}


def main():
    while True:
        print(MENU)
        choice = input("Choose an option: ")
        if choice == "0":
            print("Goodbye!")
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("Invalid choice, try again.")
            continue
        try:
            action()
        except ValueError:
            print("Invalid number entered, please try again.")


if __name__ == "__main__":
    main()
