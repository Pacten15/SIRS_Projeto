from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
import json
import sys
import base64


def read_private_key(private_key_path):
    with open(private_key_path, 'rb') as f:
        private_key = RSA.import_key(f.read())
    f.close()
    return private_key

def read_secret_key(secret_key_path):
    with open(secret_key_path, 'rb') as f:
        secret_key = f.read()
    f.close()
    return secret_key

def read_json_file(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        f.close()
        return data

def create_json_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    f.close()

def create_nonce():

    nonce = get_random_bytes(16)
    with open('nonce.txt', 'wb') as f:
        f.write(nonce)
    f.close()
    return nonce



def create_iv():
    iv = get_random_bytes(16)
    with open('iv.txt', 'wb') as f:
        f.write(iv)
    f.close()
    return iv



def write_signature_to_file(file_path, private_key_path, nonce):
    # Load the private key
    private_key = read_private_key(private_key_path)

    # open Json file
    data = read_json_file(file_path)

    # Convert the JSON object to a byte array
    jsonString = json.dumps(data ,indent=4)
    documentBytes = jsonString.encode()

    

    # Generate the digital signature
    h = SHA256.new(documentBytes + nonce)
    signature = pkcs1_15.new(private_key).sign(h)

    # Add the signature to the JSON object
    signatureEncode64 = base64.b64encode(signature)
    data['__SIGN'] = signatureEncode64.decode()

    return data

def encrypt_file(file_path, secret_key_path, iv):

    # Load the secret key
    secret_key = read_secret_key(secret_key_path)

    # open Json file
    data = read_json_file(file_path)

    # Convert the JSON object to a byte array
    jsonString = json.dumps(data)
    documentBytes = jsonString.encode()

    # Encrypt the JSON object
    cipher = AES.new(secret_key, AES.MODE_CBC, iv)
    ciphered_data = cipher.encrypt(pad(documentBytes, AES.block_size))

    # create file with encrypted data
    with open('encrypted_file', 'wb') as f:
        f.write(ciphered_data)
        f.close()

def main(file_path, modified_file_name, private_key_path, secret_key_path):

    nonce = create_nonce()

    # Write signature to file
    data = write_signature_to_file(file_path, private_key_path, nonce)

    # Write JSON object to file
    create_json_file(modified_file_name, data)

    # Encrypt file
    iv = create_iv()
    data = encrypt_file(modified_file_name, secret_key_path, iv)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])