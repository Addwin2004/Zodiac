from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Retrieve API key from environment variables
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

def format_gemini_response(text):
    """Clean and convert Gemini output to HTML-friendly format."""
    text = text.replace("**", "").replace("##", "").replace("*", "")
    text = text.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return f"<p>{text}</p>"

def is_valid_email_input(text):
    """
    Loosens the validation to allow emails without explicit headers.
    Checks for any combination of features: email address, link, formal greeting, or multi-line format.
    """
    if not text or not isinstance(text, str):
        return False

    email_features = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',  # Email addresses
        r'http[s]?://',                                       # URLs
        r'^(Dear|Hi|Hello)\b',                                # Common greetings at start
        r'\n.*\n.*'                                           # Multiline (2+ lines)
    ]

    for pattern in email_features:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            return True

    return False


# Route for the main page
@app.route('/')
def index():
    """Render the main phishing detection interface."""
    return render_template('index.html')

# Route to analyze the submitted email
@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze the provided email text using the Gemini API and return the result.

    Returns:
        JSON response with analysis result or error message.
    """
    # Extract email text from the form
    email_text = request.form['email']

    # Validate input
    if not is_valid_email_input(email_text):
        return jsonify({'result': format_gemini_response("This is not an email. Please provide a valid email text containing headers, URLs, or an email address.")}), 400

    # Prepare payload for API request
    payload = {
        "contents": [{
            "parts": [{
                "text": f"You are a cybersecurity expert. Analyze the following text and determine if it is a phishing email. If it's not an email, simply respond: 'This is not an email'. Make sure that the output you give looks professional and well-formatted so that a normal user can understand it easily.Say Wheather it is 'Phishing' or 'not a phishing' in the output.Provide your confidence level in percentage (0–100%) and tell the reasons in small points.make it short.Always classify emails strictly based on these phishing indicators: - Fake sender domains- Suspicious links- Urgent action- Requesting login credentials or payments.If the email does not meet these criteria, do not mark it as phishing. \n\n{email_text}"
            }]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 1,
            "topP": 1
        }
    }

    # Set request headers
    headers = {'Content-Type': 'application/json'}

    try:
        # Send request to Gemini API
        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload)

        # Process API response
        if response.status_code == 200:
            data = response.json()
            reply = data['candidates'][0]['content']['parts'][0]['text']
            formatted_reply = format_gemini_response(reply)
            return jsonify({'result': formatted_reply})
        else:
            return jsonify({'result': f'API Error: {response.status_code}. Please try again later.'}), 500
    except Exception as e:
        return jsonify({'result': f'Error: {str(e)}. Please try again later.'}), 500

if __name__ == '__main__':
    # Run the Flask app in debug mode
    app.run(debug=True)
