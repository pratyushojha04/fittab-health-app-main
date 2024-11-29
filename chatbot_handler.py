from flask import Blueprint, jsonify, request
import os
import google.generativeai as genai
import markdown
import bleach

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

GEMINI_API_KEY = 'AIzaSyBkQIdA1jCtK_C-l9GWS0yzh73UG61jeGU'
genai.configure(api_key=GEMINI_API_KEY)

# Configure allowed HTML tags and attributes for safe rendering
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'code', 'pre']
ALLOWED_ATTRIBUTES = {'*': ['class']}

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        message = request.json.get('message')
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate response
        prompt = f"""You are a fitness assistant. Respond to the following message in a helpful and encouraging way.
                    Format your response with markdown for better readability.
                    Use bullet points for lists, bold for important terms, and code blocks for exercises or routines.
                    Message: {message}"""
        
        response = model.generate_content(prompt)
        
        if not response.text:
            return jsonify({'error': 'No response generated'}), 500

        # Convert markdown to HTML and sanitize
        html_response = markdown.markdown(response.text)
        sanitized_html = bleach.clean(
            html_response,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return jsonify({
            'response': response.text,
            'html_response': sanitized_html
        })

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500
