import sys

try:
    import BombAppetit as BA
except ImportError:
    print("Import failed. Install dependencies with: pip3 install -r requirements.txt")

def print_help():
    print("Usage:")
    print(f"    python3 {sys.argv[0]} (action) (infile) (src_key) (dst_key) (outfile)")
    print("\n  Actions:")
    print("    help      - Prints this message")
    print("    protect   - Encrypts (infile), (src_key) is private, (dst_key) is public")
    print("    unprotect - Decrypts (infile), (src_key) is public,  (dst_key) is private")
    print("    check     - Tests (infile), same arguments as unprotect, no (outfile)")

def main():
    if len(sys.argv) < 2: # name, action
        print_help()
        print("\nERROR: missing arguments", file=sys.stderr)
        exit(1)

    _, action = sys.argv[:2]

    if action not in ('help', 'protect', 'unprotect', 'check'):
        print_help()
        print(f"\nERROR: unknown action '{action}'", file=sys.stderr)
        exit(1)

    if action == 'help':
        print_help()
        exit(0)

    if (len(sys.argv) < 5 and action == 'check') or len(sys.argv) < 6: # name, action, input, src, dst
        print_help()
        print("\nERROR: missing arguments", file=sys.stderr)
        exit(1)

    _, action, infile_path, src_key_path, dst_key_path = sys.argv[:5]

    if action == 'check':
        BA.check(infile_path, src_key_path, dst_key_path)

    outfile_path = sys.argv[5]

    if action == 'protect':
        BA.protect(infile_path, src_key_path, dst_key_path, outfile_path)

    if action == 'unprotect':
        BA.unprotect(infile_path, src_key_path, dst_key_path, outfile_path)

if __name__ == "__main__":
    main()
