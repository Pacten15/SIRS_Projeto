from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
import json
import sys
import base64


#Auxiliary functions

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

def read_random_bytes_or_encrypted_files_bytes(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    f.close()
    return data

def read_private_key(private_key_path):
    with open(private_key_path, 'rb') as f:
        private_key = RSA.import_key(f.read())
    f.close()
    return private_key

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


#functions envolved in the decryption of the file and verification of the signature

def decrypt_file(file_path, secret_key_path, iv_path):
    # Load the secret key
    secret_key = read_secret_key(secret_key_path)
    # Load the iv
    iv = read_random_bytes_or_encrypted_files_bytes(iv_path)
    # Load the encrypted file
    encrypted_file = read_random_bytes_or_encrypted_files_bytes(file_path)
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
    nonce = read_random_bytes_or_encrypted_files_bytes(nonce_path)
    
    # Load the decrypted file
    data = json.loads(decrypted_file_bytes.decode())

    # Load the signature
    signature_bytes = base64.b64decode(data['__SIGN'].encode())

    # Remove the signature from the data
    data.pop('__SIGN', None)

    # Convert the JSON object to a byte array
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
    
#----------------------------------------------------------------#


#functions to write the signature to the file and ecryption of the file
    
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


#-------------------------------------------------------------------------#

#functions refered in the Project Overview


def protect(file_path,modified_file_name, public_key_path, secret_key_path):
    nonce = create_nonce()
    iv = create_iv()
    list = [nonce, iv]
    data = write_signature_to_file(file_path, public_key_path, nonce)
    create_json_file(modified_file_name, data)
    encrypt_file(data, secret_key_path, iv)
    return list

def unprotect(file_path, secret_key_path, iv_path):
    decrypted_file_bytes = decrypt_file(file_path, secret_key_path, iv_path)
    decrypted_data_readable = json.loads(decrypted_file_bytes)
    new_file_path = file_path.split('.')[0] + '_decrypted.json'
    create_json_file(new_file_path, decrypted_data_readable)
     

def check(file_path,public_key_path, nonce_path):
    data = read_json_file(file_path)
    
     # Convert the JSON object to a byte array
    jsonString = json.dumps(data ,indent=4)
    documentBytes = jsonString.encode()

    verify_signature(documentBytes, public_key_path , nonce_path)


