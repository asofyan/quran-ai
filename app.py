from flask import Flask, Response, request, jsonify
from flask_cors import CORS  # Enable Cross-Origin Resource Sharing (CORS)
from http import HTTPStatus
from dashscope import Application
import dashscope
import json
import logging
import jwt
import datetime

# === Configuration ===
SECRET_KEY = "qFmpJiFInP"  # Secret key for JWT token generation
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'  # DashScope API endpoint
APP_ID = 'your_app_id_here'  # Replace with your actual Application ID from DashScope

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow frontend to communicate with backend

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# === JWT Token Generation and Verification ===
def generate_jwt():
    """
    Generate a JWT token for frontend authentication.
    The token expires after 1 hour.
    """
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # Expiration time
        "iat": datetime.datetime.utcnow()  # Issued at time
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")  # Encode the token
    return token


def verify_jwt(token):
    """
    Verify the JWT token in incoming requests.
    Returns True if the token is valid, False otherwise.
    """
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  # Decode and verify the token
        return True
    except jwt.ExpiredSignatureError:
        logging.error("JWT token has expired.")
        return False
    except jwt.InvalidTokenError:
        logging.error("Invalid JWT token provided.")
        return False


# === Endpoints ===
@app.route('/token', methods=['GET'])
def get_token():
    """
    Endpoint for frontend to retrieve a JWT token.
    This token is required for authenticating subsequent requests.
    """
    token = generate_jwt()
    return jsonify({"token": token})


@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint for handling chat interactions with the AI model.
    - Authenticates the user using JWT.
    - Sends the full response from the DashScope API in one go (non-streaming).
    """
    # Step 1: Authenticate the request using JWT
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logging.warning("Unauthorized request: Missing or invalid Authorization header.")
        return jsonify({"error": "Unauthorized"}), 401  # Unauthorized error

    token = auth_header.split(" ")[1]  # Extract the token from the header
    if not verify_jwt(token):
        logging.warning("Invalid or expired JWT token.")
        return jsonify({"error": "Invalid or expired token"}), 403  # Forbidden error

    # Step 2: Parse the incoming JSON data
    data = request.json
    user_message = data.get("message")
    if not user_message:
        logging.warning("No message provided in the request.")
        return jsonify({"error": "Message is required"}), 400  # Bad Request error

    logging.debug(f"Received message: {user_message}")

    # Step 3: Query DashScope API for a full response (non-streaming)
    try:
        response = Application.call(
            app_id='c82d9c94f922432b9c189bfa4e1dc5f0',
            prompt=user_message,
            stream=False,  # Disable streaming mode
            incremental_output=False  # Disable incremental output
        )

        if response.status_code != HTTPStatus.OK:
            # Log and return an error message if the API call fails
            logging.error(
                f"Error response: request_id={response.request_id}, "
                f"code={response.status_code}, message={response.message}"
            )
            return jsonify({"error": response.message}), response.status_code

        # Extract the full text output from the API response
        output = response.output.get("text", "").strip()
        if not output:
            logging.warning("Empty response received from DashScope API.")
            return jsonify({"error": "No response generated."}), 500  # Internal Server Error

        logging.debug(f"Full response: {output}")
        return jsonify({"text": output})  # Return the full response as JSON

    except Exception as e:
        # Handle unexpected errors during API interaction
        logging.error(f"Unexpected error during API call: {str(e)}")
        return jsonify({"error": "An unexpected error occurred."}), 500  # Internal Server Error


# === Main Execution ===
if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Run the Flask app on port 5000