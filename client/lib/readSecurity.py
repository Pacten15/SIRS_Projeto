from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
import json
import sys
import base64
from Crypto.Util.Padding import unpad


def read_public_key(public_key_path):
    try:
        with open(public_key_path, 'rb') as f:
            public_key = RSA.import_key(f.read())
        f.close()
        return public_key
    except IOError:
        print(f"File `{public_key_path}' could not be opened.", file=sys.stderr)
        exit(1)

def read_secret_key(secret_key_path):
    with open(secret_key_path, 'rb') as f:
        secret_key = f.read()
    f.close()
    return secret_key

def read_file(file_path):
        with open(file_path, 'r') as f:
            data = f.read()
        f.close()
        return data

def read_random_bytes_or_encrypted_files(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    f.close()
    return data


def decrypt_file(file_path, secret_key_path, iv_path):
    # Load the secret key
    secret_key = read_secret_key(secret_key_path)
    # Load the iv
    iv = read_random_bytes_or_encrypted_files(iv_path)
    # Load the encrypted file
    encrypted_file = read_random_bytes_or_encrypted_files(file_path)
    # Create the cipher object and decrypt the data
    cipher = AES.new(secret_key, AES.MODE_CBC, iv)
    decrypted_data = cipher.decrypt(encrypted_file)
    # Unpad the data
    original_data = unpad(decrypted_data, AES.block_size)
    
    return original_data

def verify_signature(decrypted_file_bytes, public_key_path, nonce_path):
    # Load the public key
    public_key = read_public_key(public_key_path)

    # Load the nonce
    nonce = read_random_bytes_or_encrypted_files(nonce_path)
    
    # Load the decrypted file
    data = json.loads(decrypted_file_bytes.decode())

    signature_bytes = base64.b64decode(data['__SIGN'].encode())

    data.pop('__SIGN', None)

    document_bytes = json.dumps(data, indent=4).encode()


    # Verify signature
    h = SHA256.new(document_bytes + nonce)
    try:
        pkcs1_15.new(public_key).verify(h, signature_bytes)
        print("The signature is valid.")
        return True
    except (ValueError, TypeError):
        print("The signature is not valid.")
        return False
    

def main(file_path, secret_key_path, iv_path, public_key_path, nonce):
    decrypted_file_bytes = decrypt_file(file_path, secret_key_path, iv_path)
    verify_signature(decrypted_file_bytes, public_key_path , nonce)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Argument(s) missing!", file=sys.stderr)
        print(f"Usage: python3 {sys.argv[0]} <file.json> <secret.key> <iv.txt> <publicRSA.key>", file=sys.stderr)
        exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    





