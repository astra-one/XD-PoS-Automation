import base64
import re
import argparse

class Decrypter:
    def decrypt(self, method, s):
        if method == 'asc':
            return self.decrypt_asc(s)
        elif method == 'base':
            return self.decrypt_base(s)
        else:
            raise ValueError(f"Unknown decryption method: {method}")

    def decrypt_asc(self, s):
        # Shift each character backward by 2 positions in the ASCII table
        result = ''.join(chr(ord(c) - 2) for c in s)
        return result

    def decrypt_base(self, s):
        # Decode Base64 for selected parts enclosed in <b64></b64> tags
        def decode_match(match):
            b64_string = match.group(1)
            decoded_bytes = base64.b64decode(b64_string)
            return decoded_bytes.decode('utf-8')

        # Use regex to find all <b64>...</b64> sections and decode them
        pattern = r'<b64>(.*?)</b64>'
        result = re.sub(pattern, decode_match, s)
        return result

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Decrypt a string using the specified method.')
    parser.add_argument('method', choices=['asc', 'base'], help='Decryption method to use (asc or base).')
    parser.add_argument('string', help='The string to decrypt.')
    args = parser.parse_args()

    decrypter = Decrypter()
    try:
        decrypted_string = decrypter.decrypt(args.method, args.string)
        print(decrypted_string)
    except Exception as e:
        print(f"Error during decryption: {e}")
