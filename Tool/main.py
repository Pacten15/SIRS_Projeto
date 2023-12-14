import sys
import json

sys.path.append('..')
try:
    import BombAppetit as BA
except ImportError:
    print("Import failed. Install dependencies with: pip3 install -r requirements.txt")

def print_help():
    print("Usage:")
    print(f"    python3 {sys.argv[0]} (action) (infile) (src_key) (dst_key) (outfile)")
    print("\n  Actions:")
    print("    help      - Prints this message")
    print("    generate  - Generates a new RSA private key, (outfile) only")
    print("    protect   - Encrypts (infile), (src_key) is private, (dst_key) is public")
    print("    unprotect - Decrypts (infile), (src_key) is public,  (dst_key) is private")
    print("    check     - Tests (infile), same arguments as unprotect, no (outfile)")

def protect(infile_path, src_key_path, dst_key_path, outfile_path):
    with open(infile_path, 'r') as f:
        infile = json.load(f)

    src_priv_key, _ = BA.load_keypair(src_key_path)
    if src_priv_key is None:
        print("ERROR: source key is not a private key", file=sys.stderr)
        exit(1)
    
    _, dst_pub_key = BA.load_keypair(dst_key_path)
    if dst_pub_key is None:
        print("ERROR: destination key is not a public key", file=sys.stderr)
        exit(1)

    outfile = BA.encrypt_json(infile, src_priv_key, dst_pub_key)

    with open(outfile_path, 'w') as f:
        json.dump(outfile, f)

def unprotect(infile_path, src_key_path, dst_key_path, outfile_path):
    with open(infile_path, 'r') as f:
        infile = json.load(f)

    if 'content' not in infile or 'signature' not in infile:
        print("ERROR: input file is not a valid encrypted document", file=sys.stderr)
        exit(1)

    _, src_pub_key = BA.load_keypair(src_key_path)
    if src_pub_key is None:
        print("ERROR: source key is not a public key", file=sys.stderr)
        exit(1)
    
    dst_priv_key, _ = BA.load_keypair(dst_key_path)
    if dst_priv_key is None:
        print("ERROR: destination key is not a private key", file=sys.stderr)
        exit(1)

    outfile, _ = BA.decrypt_json(infile, src_pub_key, dst_priv_key)

    with open(outfile_path, 'w') as f:
        json.dump(outfile, f, indent=4)

def check(infile_path, src_key_path, dst_key_path):
    with open(infile_path, 'r') as f:
        infile = json.load(f)

    if 'content' not in infile or 'signature' not in infile:
        print("ERROR: input file is not a valid encrypted document", file=sys.stderr)
        exit(1)

    _, src_pub_key = BA.load_keypair(src_key_path)
    if src_pub_key is None:
        print("ERROR: source key is not a public key", file=sys.stderr)
        exit(1)
    
    dst_priv_key, _ = BA.load_keypair(dst_key_path)
    if dst_priv_key is None:
        print("ERROR: destination key is not a private key", file=sys.stderr)
        exit(1)

    try:
        BA.decrypt_json(infile, src_pub_key, dst_priv_key)
        print("OK: document is valid")
    except Exception as e:
        print("ERROR: document is invalid", file=sys.stderr)
        exit(1) 


def main():
    if len(sys.argv) < 2: # name, action
        print_help()
        print("\nERROR: missing arguments", file=sys.stderr)
        exit(1)

    _, action = sys.argv[:2]

    if action not in ('help', 'protect', 'unprotect', 'check', 'generate'):
        print_help()
        print(f"\nERROR: unknown action '{action}'", file=sys.stderr)
        exit(1)

    if action == 'help':
        print_help()
        exit(0)
    
    if action == 'generate' and len(sys.argv) < 3: # name, action, outfile_path
        print_help()
        print("\nERROR: missing arguments", file=sys.stderr)
        exit(1)
    
    if action == 'generate':
        _, _, outfile_path = sys.argv[:3]
        BA.create_keypair(filename=outfile_path)
        exit(0)

    if (len(sys.argv) < 4 and action == 'check') or len(sys.argv) < 5: # name, action, input, src, dst
        print_help()
        print("\nERROR: missing arguments", file=sys.stderr)
        exit(1)

    _, action, infile_path, src_key_path, dst_key_path = sys.argv[:5]

    if action == 'check':
        check(infile_path, src_key_path, dst_key_path)
        exit(0)

    outfile_path = sys.argv[5]

    if action == 'protect':
        protect(infile_path, src_key_path, dst_key_path, outfile_path)

    if action == 'unprotect':
        unprotect(infile_path, src_key_path, dst_key_path, outfile_path)

if __name__ == "__main__":
    main()
