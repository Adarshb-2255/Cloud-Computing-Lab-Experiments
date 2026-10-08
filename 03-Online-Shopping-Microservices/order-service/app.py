from flask import Flask, jsonify
import requests

app = Flask(__name__)

PRODUCT_SERVICE = "http://product-service:5000"
USER_SERVICE = "http://user-service:5000"


@app.route("/order")
def create_order():

    user_response = requests.get(
        f"{USER_SERVICE}/user/1"
    )

    product_response = requests.get(
        f"{PRODUCT_SERVICE}/product/1"
    )

    if user_response.status_code != 200:
        return jsonify({
            "error": "User Service unavailable"
        }), 500

    if product_response.status_code != 200:
        return jsonify({
            "error": "Product Service unavailable"
        }), 500

    user = user_response.json()
    product = product_response.json()

    order = {
        "message": "Order created successfully",
        "user": user,
        "product": product
    }

    return jsonify(order)


@app.route("/health")
def health():

    return jsonify({
        "service": "Order Service",
        "status": "running"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )