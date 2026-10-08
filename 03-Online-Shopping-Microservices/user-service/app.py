from flask import Flask, jsonify

app = Flask(__name__)

users = {
    1: {
        "id": 1,
        "name": "Adarsh",
        "email": "adarsh@example.com"
    },
    2: {
        "id": 2,
        "name": "Rahul",
        "email": "rahul@example.com"
    },
    3: {
        "id": 3,
        "name": "Ramesh",
        "email": "ramesh@example.com"
    }
}


@app.route("/user/<int:user_id>")
def get_user(user_id):

    user = users.get(user_id)

    if user:
        return jsonify(user)

    return jsonify({"error": "User not found"}), 404


@app.route("/health")
def health():

    return jsonify({
        "service": "User Service",
        "status": "running"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)