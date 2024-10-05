import requests

# URL and credentials
TEST_URL = "https://myxd1.azurewebsites.net"
LOGIN_ENDPOINT = f"{TEST_URL}/oauth/token"
ADMIN = "info@xd.pt"
ADMIN_PASSWORD = "xd"
CLIENT_ID = "mobileapps"

# Headers and payload for the authentication request
headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

# Payload for the client credentials grant type
payload = {
    'client_id': CLIENT_ID,
    'client_secret': ADMIN_PASSWORD,  # Assuming the password is used as the client secret here
    'grant_type': 'client_credentials'
}

# Make the POST request to the OAuth token endpoint
response = requests.post(LOGIN_ENDPOINT, headers=headers, data=payload)

# Check if the authentication was successful
if response.status_code == 200:
    print("Authentication successful!")
    print("Response:", response.json())
else:
    print("Authentication failed!")
    print(f"Status Code: {response.status_code}")
    print("Response:", response.text)
