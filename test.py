import requests

def visit_website():
    url = 'https://cryotank-nus.streamlit.app'  # Replace with the URL of the website you want to visit
    response = requests.get(url)
    print(f"Website visited - Status code: {response.status_code}")

visit_website()