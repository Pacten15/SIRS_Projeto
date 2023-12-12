import json
import requests
import sys
sys.path.append('../tool/BombAppetit')

from functions import create_key_pair
from functions import encrypt


def read_json_file(file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print("File not found.")
            return None
        except json.JSONDecodeError:
            print("Invalid JSON format.")
            return None
    
class ClientInterface:
    def __init__(self, base_url , username):
        self.base_url = base_url
        self.username = username

    def register_user(self, username):

        try:
            # Create key pair
            keys = create_key_pair(2048, 'keys/' + username + '.pubkey', 'keys/' + username + '.privkey')

            public_key = keys[0]

            # Create user data dictionary
            user_data = {
                'name': username,
                'public_key': public_key
            }

            response = requests.post(self.base_url + '/users', json=user_data)
            return response.status_code
        except requests.exceptions.RequestException as e:
            print("Error: Failed to connect to remote server.", e)
            return None


    def read_remote_json_file(self, file_path):
        try:

            response = requests.get(self.base_url + '/read/' + file_path)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print("Failed to read remote JSON file. Status code:", response.status_code)
                return None
        except requests.exceptions.RequestException as e:
            print("Error: Failed to connect to remote server.", e)
            return None

    def update_remote_json_file(self, file_path, data):
        try:
            response = requests.put(self.base_url + '/update/' + file_path, json=data)
            return response.status_code
        except requests.exceptions.RequestException as e:
            print("Error: Failed to connect to remote server.", e)
            return None

    def delete_remote_json_file(self, file_path):
        try:
            response = requests.delete(self.base_url + '/delete/' + file_path)
            return response.status_code
        except requests.exceptions.RequestException as e:
            print("Error: Failed to connect to remote server.", e)
            return None

    def create_request(self):

        print("Entering in the cryptography interface: \n")
        print("Exiting the cryptography interface: \n")
        data = read_json_file('encrypted.json')
        if data is not None:
            try:
                response = requests.post(self.base_url + '/create', json=data)
                return response.status_code
            except requests.exceptions.RequestException as e:
                print("Error: Failed to connect to remote server.", e)
                return None
        else:
            return None

    def help_command(self):
        print("Available commands:")
        print("1. Create request")
        print("2. Read remote JSON file")
        print("3. Update remote JSON file")
        print("4. Delete remote JSON file")
        print("5. Exit")

    def run_interface(self):
        while True:

            self.register_user(self.username)

            self.help_command()

            choice = input("Enter your choice: ")

            if choice == "1":
                file_path = input("Enter the file path: ")
                status_code = self.create_request(file_path)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            elif choice == "2":
                file_path = input("Enter the file path: ")
                data = self.read_remote_json_file(file_path)
                if data is not None:
                    print("Remote JSON file data:", data)
                else:
                    print("Failed to read remote JSON file")
            elif choice == "3":
                file_path = input("Enter the file path: ")
                data = input("Enter the updated data: ")
                status_code = self.update_remote_json_file(file_path, data)
                if status_code is not None:
                    print("Update status code:", status_code)
                else:
                    print("Failed to update remote JSON file")
            elif choice == "4":
                file_path = input("Enter the file path: ")
                status_code = self.delete_remote_json_file(file_path)
                if status_code is not None:
                    print("Delete status code:", status_code)
                else:
                    print("Failed to delete remote JSON file")
            elif choice == "5":
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    base_url = "http://192.168.1.254:5000/api"  # Replace with your actual base URL
    username = input("Enter your username: ")
    client = ClientInterface(base_url, username)
    client.run_interface()

   
