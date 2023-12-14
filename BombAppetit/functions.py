
import sys
import json
from datetime import datetime
from base64 import b64encode, b64decode

from Crypto.Cipher       import AES, PKCS1_v1_5
from Crypto.Hash         import SHA256
from Crypto.PublicKey    import RSA
from Crypto.Random       import get_random_bytes
from Crypto.Signature    import pkcs1_15
from Crypto.Util.Padding import pad, unpad

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

def create_key_pair(key_size, public_key_path, private_key_path):
    ''' Creates a RSA key pair of the given key_size in bytes and writes the public key and private key to separate files. '''
    try:
        key = RSA.generate(key_size)
    except ValueError:
        print(f"ERROR: Invalid key size '{key_size}'.", file=sys.stderr)
        exit(1)
    
    # Write public key to file
    with open(public_key_path, 'wb') as public_key_file:
        public_key_file.write(key.publickey().export_key())

    # Write private key to file
    with open(private_key_path, 'wb') as private_key_file:
        private_key_file.write(key.export_key())
    
    return [key.publickey().export_key(), key.export_key()]

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

    encrypted_document = encrypt_json_section(raw_content, src_private_key, dst_public_key, 'mealVoucher')
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
        raw_content = decrypt_json_section(encrypted_document, src_public_key, dst_private_key, nonces, 'mealVoucher')
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


def encrypt_json_section(raw_bytes, src_private_key, dst_public_key, section):
    ''' Encrypts content using generated AES key, AES key will be encrypted
    with dst_public_key for confidentiality, the contents will be hashed,
    for integrity, and signed using src_private_key, for autheticity.'''


    decrypted_Documents = json.loads(raw_bytes)

    section_content = decrypted_Documents['restaurantInfo'][section]

    section_bytes = json.dumps(section_content).encode('utf-8')

    # Generate AES key and encrypt contents
    gen_key = get_random_bytes(32) # 32 for AES-256
    gen_cipher = AES.new(gen_key, AES.MODE_CBC)
    ciphertext = gen_cipher.encrypt(pad(section_bytes, AES.block_size))
    section_content = b64encode(ciphertext).decode('utf-8')
    decrypted_Documents['restaurantInfo'][section] = section_content
    encrypted_content = b64encode(json.dumps(decrypted_Documents).encode('utf-8')).decode('utf-8')

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


def decrypt_json_section(encrypted_document, src_public_key, dst_private_key, nonces, section):
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


    encrypted_content_bytes = b64decode(encrypted_content.encode('utf-8'))

    decrypted_Documents = json.loads(encrypted_content_bytes.decode('utf-8'))

    section_content = decrypted_Documents['restaurantInfo'][section]

    section_bytes = b64decode(section_content.encode('utf-8'))

    # Decrypt content with AES key and IV
    ciphertext = section_bytes
    gen_cipher = AES.new(gen_key, AES.MODE_CBC, gen_iv)
    raw_content = unpad(gen_cipher.decrypt(ciphertext), AES.block_size)

    decrypted_Documents['restaurantInfo'][section] = json.loads(raw_content)

    print(decrypted_Documents)

    decrypted_Documents_bytes = json.dumps(decrypted_Documents, indent=2, ensure_ascii=False).encode('utf-8')

    return decrypted_Documents_bytes


# --- New functions for the new structure ---

# -- output of encrypt_json() and input of decrypt_json() --
#
# encrypted_document = {
#     'content':       str( {    
#                          'json': json_object,
#                          'timestamp': seconds in float with microsecond precision,
#                          'encrypted_sections': list,
#                          'fully_encrypted': bool
#                      } ),
#     'encrypted_key': base64(rsa_encrypt(AES_key + AES_IV)),
#     'signature':     base64(rsa_sign(sha256(encrypted_content))),
# }
#

def encrypt_json(json_object, src_private_key, dst_public_key, sections_to_encrypt=None):
    ''' Encrypts content using generated AES key, AES key will be encrypted
        with dst_public_key for confidentiality, the contents will be hashed,
        for integrity, and signed using src_private_key, for autheticity.
        
        sections_to_encrypt is a list of strings, each string is a path to a
        section of the JSON that should be encrypted. If sections_to_encrypt is
        None, the entire JSON will be encrypted. If sections_to_encrypt is an
        empty list, nothing will be encrypted.'''
    # Generate AES key and encrypt contents
    gen_key = get_random_bytes(32) # 32 for AES-256
    gen_cipher = AES.new(gen_key, AES.MODE_CBC)

    json_mutable = json_object.copy()

    if sections_to_encrypt is None:
        # -- encrypt entire json --
        json_bytes = json.dumps(json_mutable).encode('utf-8')
        ciphertext = gen_cipher.encrypt(pad(json_bytes, AES.block_size))
        json_mutable = b64encode(ciphertext).decode('utf-8')
    else:
        # -- encrypt only the specified sections --
        for section in sections_to_encrypt:
            # remove the section from the json
            content = json_mutable.get(section, None)
            if content is None:
                print(f"WARNING: section '{section}' not found in JSON")
                continue

            # encrypt the section
            json_bytes = json.dumps(content).encode('utf-8')
            ciphertext = gen_cipher.encrypt(pad(json_bytes, AES.block_size))
            encrypted_content = b64encode(ciphertext).decode('utf-8')

            # replace the section in the json
            json_mutable[section] = encrypted_content

    json_bytes = json.dumps({
        'json': json_mutable,
        'timestamp': datetime.utcnow().timestamp(),
        'encrypted_sections': sections_to_encrypt,
        'fully_encrypted': sections_to_encrypt is None,
    })

    # Encrypt AES key and IV with public RSA key
    rsa_cipher = PKCS1_v1_5.new(dst_public_key)
    ciphertext = rsa_cipher.encrypt(gen_key + gen_cipher.iv) # this concatenates the bytes
    encrypted_key = b64encode(ciphertext).decode('utf-8')

    # Create contents digest and sign
    hashed = SHA256.new(json_bytes.encode('utf-8'))
    signer = pkcs1_15.new(src_private_key)
    ciphertext = signer.sign(hashed)
    encrypted_hash = b64encode(ciphertext).decode('utf-8')

    return { 'content':       json_bytes,
             'encrypted_key': encrypted_key,
             'signature':     encrypted_hash, }

def decrypt_json(encrypted_document, src_public_key, dst_private_key, seen_ivs=None):
    ''' Decrypts encrypted_document using AES, AES key is found by decrypting
        with dst_private_key, the signature is checked using src_public_key,
        and the decrypted contents are returned directly.'''
    content       = encrypted_document.get('content')
    encrypted_key = encrypted_document.get('encrypted_key')
    if seen_ivs is None:
        seen_ivs = set()

    # Decrypt AES key and IV with private RSA key
    sentinel = get_random_bytes(32 + 16)
    rsa_cipher = PKCS1_v1_5.new(dst_private_key)
    ciphertext = b64decode(encrypted_key.encode())
    gen_key_iv = rsa_cipher.decrypt(ciphertext, sentinel, expected_pt_len=32 + 16)
    assert gen_key_iv != sentinel

    gen_key = gen_key_iv[:32]
    gen_iv  = gen_key_iv[32:32+16]
    gen_cipher = AES.new(gen_key, AES.MODE_CBC, gen_iv)

    root_json = json.loads(content)
    if root_json['fully_encrypted']:
        # -- decrypt entire json --
        decoded_content = b64decode(root_json['json'].encode('utf-8'))
        raw_content = unpad(gen_cipher.decrypt(decoded_content), AES.block_size)
        json_mutable = json.loads(raw_content)
    else:
        # -- decrypt only the specified sections --
        json_mutable = root_json['json']
        for section in root_json['encrypted_sections']:
            # remove the section from the json
            decoded_content = json_mutable.get(section, None)
            if decoded_content is None:
                print(f"WARNING: section '{section}' not found in JSON")
                continue
            decoded_content = b64decode(decoded_content.encode('utf-8'))

            # decrypt the section
            raw_content = unpad(gen_cipher.decrypt(decoded_content), AES.block_size)

            # replace the section in the json
            json_mutable[section] = json.loads(raw_content)

    # Test timestamp for freshness
    now = datetime.utcnow().timestamp() - 5 # 5 second leeway
    if root_json['timestamp'] < now:
        print("WARNING: freshness check failed, timestamp is too old")
    
    if gen_iv in seen_ivs:
        print("WARNING: freshness check failed, IV has been seen before")

    # This will raise an exception if the signature is invalid
    test_json_hash(encrypted_document, src_public_key)

    return json_mutable, gen_iv

def test_json_hash(encrypted_document, src_public_key):
    ''' Tests the hash/signature of a JSON object. Ignores freshness.'''
    content = encrypted_document.get('content')
    signature = encrypted_document.get('signature')

    # Test raw_content with the signed digest
    hashed = SHA256.new(content.encode('utf-8'))
    signer = pkcs1_15.new(src_public_key)
    signature = b64decode(signature.encode())
    signer.verify(hashed, signature)


def create_keypair(key_size=2048, filename=None):
    ''' Generates a new RSA keypair and returns it as a tuple of public and
        private keys.'''
    print(key_size)
    private_key = RSA.generate(key_size)
    public_key  = private_key.publickey()

    if filename is not None:
        save_keypair(filename, private_key)

    return private_key, public_key

def load_keypair(filename):
    ''' Loads a keypair from a file and returns it as a tuple of public and
        private keys.'''
    try:
        with open(filename, 'r') as f:
            key = RSA.import_key(f.read())
        
        if key.has_private():
            return key, key.publickey()
        else:
            return None, key
    except FileNotFoundError:
        return None, None

def save_keypair(filename, private_key):
    ''' Saves a keypair to a file.'''
    with open(filename, 'w') as f:
        f.write(private_key.export_key().decode('utf-8'))
