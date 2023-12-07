import sys
import json
from base64 import b64encode, b64decode

from Crypto.Cipher       import AES, PKCS1_v1_5
from Crypto.Hash         import SHA256
from Crypto.PublicKey    import RSA
from Crypto.Random       import get_random_bytes
from Crypto.Signature    import pkcs1_15
from Crypto.Util.Padding import pad, unpad


def read_random_bytes_or_encrypted_files(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    f.close()
    return data

def create_json_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    f.close()




def read_private_key(private_key_path):
    try:
        with open(private_key_path, 'rb') as file:
            file_content = file.read()
        private_key = RSA.import_key(file_content)
        assert private_key.has_private() == True
    except (IOError, ValueError, TypeError, AssertionError):
        print(f"ERROR: Could not read private key from file '{private_key_path}'.", file=sys.stderr)
        exit(1)
    return private_key

def read_public_key(public_key_path):
    try:
        with open(public_key_path, 'rb') as file:
            file_content = file.read()
        public_key = RSA.import_key(file_content)
        if public_key.has_private():
            print(f"WARNING: Public key '{public_key_path}' contains private key.", file=sys.stderr)
            public_key = public_key.publickey()
    except (IOError, ValueError, TypeError):
        print(f"ERROR: Could not read public key from file '{public_key_path}'.", file=sys.stderr)
        exit(1)
    return public_key

def encrypt(raw_content, src_private_key, dst_public_key):
    ''' Encrypts content using generated AES key, AES key will be encrypted
        with dst_public_key for confidentiality, the contents will be hashed,
        for integrity, and signed using src_private_key, for autheticity.'''
    # Generate AES key and encrypt contents
    gen_key = get_random_bytes(32) # 32 for AES-256
    gen_cipher = AES.new(gen_key, AES.MODE_CBC)
    ciphertext = gen_cipher.encrypt(pad(raw_content, AES.block_size))
    encrypted_content = b64encode(ciphertext).decode('utf-8')

    # Encrypt AES key and IV with public RSA key
    rsa_cipher = PKCS1_v1_5.new(dst_public_key)
    ciphertext = rsa_cipher.encrypt(gen_key+gen_cipher.iv)
    encrypted_key = b64encode(ciphertext).decode('utf-8')

    # Create contents digest and sign
    hashed = SHA256.new(encrypted_content.encode('utf-8'))
    signer = pkcs1_15.new(src_private_key)
    ciphertext = signer.sign(hashed)
    encrypted_hash = b64encode(ciphertext).decode('utf-8')

    return {"encrypted_content": encrypted_content, "encrypted_key": encrypted_key, "encrypted_hash": encrypted_hash}

def decrypt(encrypted_document, src_public_key, dst_private_key, nonces):
    ''' Decrypts encrypted_document using AES, AES key is found by decrypting
        with dst_private_key, the signature is checked using src_public_key,
        and the decrypted contents are returned directly.'''
    encrypted_content = encrypted_document['encrypted_content']
    encrypted_key = encrypted_document['encrypted_key']
    encrypted_hash = encrypted_document['encrypted_hash']
    
    # Decrypt AES key and IV with private RSA key
    sentinel = get_random_bytes(32 + 16)
    rsa_cipher = PKCS1_v1_5.new(dst_private_key)
    ciphertext = b64decode(encrypted_key.encode())
    gen_key_iv = rsa_cipher.decrypt(ciphertext, sentinel, expected_pt_len=32 + 16)
    assert gen_key_iv != sentinel
    gen_key = gen_key_iv[:32]
    gen_iv  = gen_key_iv[32:]

    # Test raw_content with the signed digest
    hashed = SHA256.new(encrypted_content.encode('utf-8'))
    signer = pkcs1_15.new(src_public_key)
    signature = b64decode(encrypted_hash.encode())
    signer.verify(hashed, signature)
    assert signature.hex() not in nonces
    nonces.append(signature.hex())

    # Decrypt content with AES key and IV
    ciphertext = b64decode(encrypted_content.encode())
    gen_cipher = AES.new(gen_key, AES.MODE_CBC, gen_iv)
    raw_content = unpad(gen_cipher.decrypt(ciphertext), AES.block_size)

    return raw_content

# --- Below are the "exposed" functions ---

def protect(infile_path, src_private_key_path, dst_public_key_path, outfile_path):
    try:
        with open(infile_path, 'rb') as infile:
            raw_content = infile.read()
        json.loads(raw_content)
    except IOError:
        print(f"ERROR: File '{infile_path}' could not be read.", file=sys.stderr)
        exit(1)
    except json.decoder.JSONDecodeError:
        print(f"ERROR: File '{infile_path}' is not a proper JSON file.", file=sys.stderr)
        exit(1)

    src_private_key = read_private_key(src_private_key_path)
    dst_public_key  = read_public_key(dst_public_key_path)

    encrypted_document = encrypt(raw_content, src_private_key, dst_public_key)
    try:
        with open(outfile_path, 'w') as outfile:
            json.dump(encrypted_document, outfile, indent=3)
    except IOError:
        print(f"ERROR: File '{outfile_path}' could not be written", file=sys.stderr)
        exit(1)

def unprotect(infile_path, src_public_key_path, dst_private_key_path, outfile_path):
    try:
        with open(infile_path, 'r') as infile:
            encrypted_document = json.load(infile)
    except IOError:
        print(f"ERROR: File '{infile_path}' could not be read.", file=sys.stderr)
        exit(1)
    except json.decoder.JSONDecodeError:
        print(f"ERROR: File '{infile_path}' is not a proper JSON file.", file=sys.stderr)
        exit(1)

    src_public_key  = read_public_key(src_public_key_path)
    dst_private_key = read_private_key(dst_private_key_path)

    try:
        with open('seen_nonces.autogen.json', 'r') as nonces_file:
            nonces = json.load(nonces_file)
    except IOError:
        nonces = []

    try:
        raw_content = decrypt(encrypted_document, src_public_key, dst_private_key, nonces)
    except (AssertionError, ValueError, KeyError):
        print("ERROR: Failed document decryption.", file=sys.stderr)
        exit(1)

    try:
        with open('seen_nonces.autogen.json', 'w') as nonces_file:
            json.dump(nonces, nonces_file)
    except IOError:
        print("WARNING: Could not store nonce to 'seen_nonces.autogen.json'.", file=sys.stderr)

    try:
        json.loads(raw_content)
        with open(outfile_path, 'wb') as outfile:
            outfile.write(raw_content)
    except IOError:
        print(f"ERROR: File '{outfile_path}' could not be written", file=sys.stderr)
        exit(1)
    except json.decoder.JSONDecodeError:
        print(f"ERROR: Decrypted file '{infile_path}' is not a proper JSON file.", file=sys.stderr)
        exit(1)

def check(infile_path, src_public_key_path, dst_private_key_path):
    try:
        with open(infile_path, 'r') as infile:
            encrypted_document = json.load(infile)
    except IOError:
        print(f"ERROR: File '{infile_path}' could not be read.", file=sys.stderr)
        exit(1)
    except json.decoder.JSONDecodeError:
        print(f"ERROR: File '{infile_path}' is not a proper JSON file.", file=sys.stderr)
        exit(1)

    src_public_key  = read_public_key(src_public_key_path)
    dst_private_key = read_private_key(dst_private_key_path)

    try:
        with open('seen_nonces.autogen.json', 'r') as nonces_file:
            nonces = json.load(nonces_file)
    except IOError:
        nonces = []

    try:
        decrypt(encrypted_document, src_public_key, dst_private_key, nonces)
    except (AssertionError, ValueError, KeyError):
        print("ERROR: Failed document verification.", file=sys.stderr)
        exit(1)

    print("Document verified!")


    def encrypt_json_section(raw_bytes, src_private_key, dst_public_key, section_bytes):
        ''' Encrypts content using generated AES key, AES key will be encrypted
        with dst_public_key for confidentiality, the contents will be hashed,
        for integrity, and signed using src_private_key, for autheticity.'''


        # Generate AES key and encrypt contents
        gen_key = get_random_bytes(32) # 32 for AES-256
        gen_cipher = AES.new(gen_key, AES.MODE_CBC)
        ciphertext = gen_cipher.encrypt(pad(raw_content, AES.block_size))
        encrypted_content = b64encode(ciphertext).decode('utf-8')

        # Encrypt AES key and IV with public RSA key
        rsa_cipher = PKCS1_v1_5.new(dst_public_key)
        ciphertext = rsa_cipher.encrypt(gen_key+gen_cipher.iv)
        encrypted_key = b64encode(ciphertext).decode('utf-8')

        # Create contents digest and sign
        hashed = SHA256.new(encrypted_content.encode('utf-8'))
        signer = pkcs1_15.new(src_private_key)
        ciphertext = signer.sign(hashed)
        encrypted_hash = b64encode(ciphertext).decode('utf-8')

        return {"encrypted_content": encrypted_content, "encrypted_key": encrypted_key, "encrypted_hash": encrypted_hash}

        

        
        
