import requests
import json
import os
import sys

# Define the base URL
BASE_URL = "http://localhost:8000/api/v1"

def color_print(text, color="white"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def simulate_n8n_ai_request():
    print("\n--- Simulating n8n AI Assessment Request ---\n")
    
    # Mock data that n8n would aggregate from previous steps
    payload = {
        "token": {
            "name": "DegenPepe",
            "symbol": "DPEPE",
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain": "sol",
            "price": 0.00042,
            "market_cap": 1500000,
            "volume_24h": 500000,
            "liquidity": 200000,
            "holder_count": 1500,
            "age_hours": 4.5
        },
        "security": {
            "is_honeypot": False,
            "is_mintable": False,
            "is_open_source": True,
            "owner_percentage": 2.5,
            "creator_percentage": 0.0
        },
        "social": {
            "twitter_followers": 5000,
            "telegram_members": 1200,
            "website_url": "https://degenpepe.io"
        },
        "safety_score": 85.0,
        "additional_info": "Developer launched a successful token last month. Community is very active on Twitter."
    }
    
    print("Sending payload to /api/v1/ai/assess...")
    try:
        response = requests.post(f"{BASE_URL}/ai/assess", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            color_print("\n✅ Success! AI Assessment Received:", "green")
            print(json.dumps(result, indent=2))
            
            # Check fields
            if "verdict" in result and "risk" in result:
                color_print(f"\nVerdict: {result['verdict']}", "cyan")
                color_print(f"Summary: {result['summary']}", "white")
                color_print(f"Explanation: {result.get('explanation', 'N/A')}", "yellow")
                color_print(f"Meme Score: {result['meme_potential_score']}/100", "magenta")
        else:
            color_print(f"\n❌ Request failed with status {response.status_code}", "red")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        color_print("\n❌ Connection Error: Is the server running?", "red")
    except Exception as e:
        color_print(f"\n❌ Error: {str(e)}", "red")

if __name__ == "__main__":
    # Check if keys are present just to warn the user
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
         color_print("WARNING: No API keys found in environment. Request will likely fail or need mocking.", "yellow")
         color_print("Run with: export OPENAI_API_KEY=sk-... or export ANTHROPIC_API_KEY=sk-...", "yellow")
    
    simulate_n8n_ai_request()
