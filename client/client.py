# CLIENT

try:
    import sys
    import os
    import argparse
    from utils.aux_functions import GeneralMethodsSecurity as gms
    
except ImportError:
    raise ImportError("Import failed. Try to install the dependencies by running: pip3 install -r requirements.txt")


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description='SIRS Project Client Interface')

    # Add arguments here
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('input_file', nargs='?', help='Input file')
    parser.add_argument('output_file', nargs='?', help='Output file')
    parser.add_argument('public_key_path', nargs='?', help='Public key file path')
    parser.add_argument('secret_key_path', nargs='?', help='Secret key file path')
    parser.add_argument('iv_path', nargs='?', help='IV file path')

    # Parse the command line arguments
    args = parser.parse_args()

    # Your code here
    if args.command == 'help':
        #print_help()
        print("none")
    elif args.command == 'protect':
        if args.input_file and args.output_file and args.public_key_path and args.secret_key_path:
            gms.protect(args.input_file, args.output_file, args.public_key_path, args.secret_key_path)
        else:
            print("Missing arguments. Usage: (tool-name) protect (input-file) (output-file) (public-key-path) (secret-key-path)")
    elif args.command == 'check':
        if args.input_file and args.public_key_path:
            gms.check(args.input_file, args.public_key_path)
        else:
            print("Missing arguments. Usage: (tool-name) check (input-file) (public-key-path)")
    elif args.command == 'unprotect':
        if args.input_file and args.secret_key_path and args.iv_path:
            gms.unprotect(args.input_file, args.secret_key_path, args.iv_path)
        else:
            print("Missing arguments. Usage: (tool-name) unprotect (input-file) (secret-key-path) (iv-path)")

if __name__ == "__main__":
    main()