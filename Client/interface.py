import json
import requests

class ClientInterface:
    def __init__(self, base_url , username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.auth = (self.username, self.password)

    def read_json_file(self, file_path):
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
    
    def create_json_file(self, file_path, data):
        try:
            with open(file_path, 'w') as file:
                json.dump(data, file)
            return True
        except IOError:
            print("Error: Failed to create JSON file.")
            return False

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

    def create_request(self, file_path):
        data = self.read_json_file(file_path)
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
    base_url = "http://example.com/api"  # Replace with your actual base URL
    client = ClientInterface(base_url)
    client.run_interface()

   


class ClientInterface:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        