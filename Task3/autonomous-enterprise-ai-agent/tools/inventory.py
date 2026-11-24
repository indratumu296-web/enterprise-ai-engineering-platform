from urllib.parse import urlencode

from utils.retry import request_json


def lookup_inventory(product: str, api_base_url: str) -> dict:
    query = urlencode({"search": product})
    products = request_json("GET", f"{api_base_url.rstrip('/')}/inventory?{query}")
    if not products:
        return {"message": f"No inventory matched '{product}'.", "products": []}
    lines = [
        f"{item['product_name']} ({item['product_id']}): {item['quantity']} available"
        for item in products
    ]
    return {"message": "\n".join(lines), "products": products}