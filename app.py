from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from http import HTTPStatus
from dashscope import Application
import dashscope
import json
import logging
import jwt
import datetime

# Konfigurasi JWT
SECRET_KEY = "qFmpJiFInP"

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

app = Flask(__name__)
CORS(app)  # Allow frontend to communicate with backend

logging.basicConfig(level=logging.DEBUG)

def generate_jwt():
    """Generate JWT for frontend"""
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "iat": datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_jwt(token):
    """Verify JWT in requests"""
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

@app.route('/token', methods=['GET'])
def get_token():
    """Endpoint for frontend to retrieve JWT"""
    token = generate_jwt()
    return jsonify({"token": token})

@app.route('/chat', methods=['POST'])
def chat():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(" ")[1]
    if not verify_jwt(token):
        return jsonify({"error": "Invalid or expired token"}), 403

    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    logging.debug(f"Received message: {user_message}")

    def stream_response():
        responses = Application.call(
            app_id='c82d9c94f922432b9c189bfa4e1dc5f0',
            prompt=user_message,
            stream=True,
            incremental_output=True
        )

        for response in responses:
            if response.status_code != HTTPStatus.OK:
                logging.error(f"Error response: request_id={response.request_id}, code={response.status_code}, message={response.message}")
                yield json.dumps({"error": response.message}) + "\n"
            else:
                output = response.output.get("text", "").strip()
                if output:
                    logging.debug(f"Streaming response: {output}")
                    yield json.dumps({"text": output}) + "\n"

    return Response(stream_response(), content_type='application/json')

if __name__ == '__main__':
    app.run(debug=True, port=5000)



from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from http import HTTPStatus
from dashscope import Application
import dashscope
import json
import logging
import sys  # Import sys to flush output

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

app = Flask(__name__)
CORS(app)  # Allow frontend to communicate with backend

logging.basicConfig(level=logging.DEBUG)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    logging.debug(f"Received message: {user_message}")

    def stream_response():
        responses = Application.call(
            app_id='c82d9c94f922432b9c189bfa4e1dc5f0',  # Replace with your actual APP ID
            prompt=user_message,
            stream=True,
            incremental_output=True
        )

        for response in responses:
            if response.status_code != HTTPStatus.OK:
                logging.error(f"Error response: request_id={response.request_id}, code={response.status_code}, message={response.message}")
                yield json.dumps({"error": response.message}) + "\n"
                sys.stdout.flush()  # Force flush
            else:
                output = response.output.get("text", "").strip()
                if output:
                    logging.debug(f"Streaming response: {output}")
                    yield json.dumps({"text": output}) + "\n"
                    sys.stdout.flush()  # Ensure real-time streaming

    return Response(stream_response(), content_type='application/json')

if __name__ == '__main__':
    app.run(debug=True, port=5000)

