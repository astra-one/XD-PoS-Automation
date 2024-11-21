import hashlib

def generate_authorization(username, terminal, credential_id):
    # Concatenate the fields in a specific order
    data = f"{username}{terminal}{credential_id}"
    
    # Hash the concatenated string using MD5
    authorization = hashlib.md5(data.encode()).hexdigest()
    return authorization

# Example values
username = "XDBR.105112"
terminal = 1
credential_id = "1d2190a9-7e40-4a74-bbda-0d248f77af6d"

# Generate the Authorization
authorization = generate_authorization(username, terminal, credential_id)
print("Generated Authorization:", authorization)
