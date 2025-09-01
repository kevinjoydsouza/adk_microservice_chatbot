import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test Gemini configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print(f"API Key loaded: {'Yes' if GOOGLE_API_KEY else 'No'}")
print(f"API Key (first 10 chars): {GOOGLE_API_KEY[:10] if GOOGLE_API_KEY else 'None'}")

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    print("✓ Gemini configured successfully")
    
    # Test model initialization
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction="You are a helpful assistant."
    )
    print("✓ Model initialized successfully")
    
    # Test simple generation
    response = model.generate_content("Hello, how are you?")
    print("✓ Content generation successful")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    print(f"Error type: {type(e).__name__}")
