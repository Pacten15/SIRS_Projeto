import sys
import json
from base64 import b64encode, b64decode

from Crypto.Cipher       import AES, PKCS1_v1_5
from Crypto.Hash         import SHA256
from Crypto.PublicKey    import RSA
from Crypto.Random       import get_random_bytes
from Crypto.Signature    import pkcs1_15
from Crypto.Util.Padding import pad, unpad

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

def main():
    key_size = 2048
    public_key_path = "keys/johnDoe.pubkey"
    private_key_path = "keys/johnDoe.privkey"

    create_key_pair(key_size, public_key_path, private_key_path)

if __name__ == "__main__":
    main()


