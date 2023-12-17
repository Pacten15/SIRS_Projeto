import json
import requests
import os 
import sys
import warnings
from urllib3.exceptions import SubjectAltNameWarning
warnings.filterwarnings('ignore', category=SubjectAltNameWarning)

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import BombAppetit as BA



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

def https_post_requests(url, data, certificate_client_path, key_path, certificate_server_path):
        try:
            response = requests.post(url, json=data, cert=(certificate_client_path, key_path), verify=certificate_server_path)
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print("Error: Failed to connect to remote server.", e)
            return None
    
class ClientInterface:
    def __init__(self, base_url, username, certificate_server_path, certificate_client_path, key_path):
        self.base_url = base_url
        self.username = ''.join(username)
        self.certificate_client_path = certificate_client_path
        self.key_path = key_path
        self.certificate_server_path = certificate_server_path
        self.privkey = None
        self.pubkey = None
        

    def register_user(self):

        # Create key pair
        keys = BA.create_key_pair(2048, 'keys/' + self.username + '.pubkey', 'keys/' + self.username + '.privkey')
        public_key = keys[0]
        # Create user data dictionary
        user_data = {
            'user_name': self.username,
            'public_key': public_key.decode(),
            'operation': 'create' 
        }

        #Load key pair
        keys = BA.load_key_pair('keys/' + self.username + '.pubkey', 'keys/' + self.username + '.privkey')
        self.pubkey = keys[0]
        self.privkey = keys[1]

        private_key = BA.str_to_key(self.privkey.decode())
        data = BA.encrypt_json(user_data, private_key, None)
        response = https_post_requests(self.base_url + '/users', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        print(response)
    
    def login_user(self):

        keys = BA.load_key_pair('keys/' + self.username + '.pubkey', 'keys/' + self.username + '.privkey')
        self.pubkey = keys[0]
        self.privkey = keys[1]

        login_data = {
            'user_name': self.username,
            'public_key': self.pubkey.decode(),
            'operation': 'login'
        }

        private_key = BA.str_to_key(self.privkey.decode())
        data = BA.encrypt_json(login_data, private_key, None)
        response = https_post_requests(self.base_url + '/users', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        print(response)

    def update_user(self, username, name):
        https_post_requests(self.base_url + '/restaurant', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
      
    def delete_user(self, username):
       data = {
           'username': username,
           'operation': 'delete'
       }
       https_post_requests(self.base_url + '/users/' + username, data, self.certificate_client_path, self.key_path, self.certificate_server_path)
       username_str = ''.join(self.username)
       os.remove('keys/' + username_str + '.pubkey')
       os.remove('keys/' + username_str + '.privkey')
        
        
      
    def create_restaurant(self, restaurantInfoPath):
        
        data = read_json_file(restaurantInfoPath)
        https_post_requests(self.base_url + '/restaurant', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
    
    def read_all_restaurants(self):
        https_post_requests(self.base_url + '/restaurant', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        

    def delete_restaurant(self, restaurantInfoId):
        https_post_requests(self.base_url + '/restaurant', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
      
        
    def update_restaurant(self, restaurantInfoId, restaurantInfoPath):
        https_post_requests(self.base_url + '/restaurant', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        

    
       
    def create_voucher(self, username, restaurantId, voucherCode, description):
    
        data = {"user_name": username,   restaurantId: restaurantId, "voucher_code": voucherCode, "description": description}
        https_post_requests(self.base_url + '/voucher', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        
        
    def update_voucher(self, voucherId, voucherCode, description):
        https_post_requests(self.base_url + '/voucher/' + voucherId, data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        
    
    def delete_voucher(self, voucherId):
        https_post_requests(self.base_url + '/voucher/' + voucherId, self.certificate_client_path, self.key_path, self.certificate_server_path)
       
    def help_command_client(self):
        print("Available commands:")
        print ("1. create user")
        print ("2. delete user")
        print ("3. read Voucher")
        print ("4. create Review")
        print ("5. read Review")
        print ("6. update Review")
        print ("7. delete Review")
        print ("8. exit")
    
    def help_command_admin(self):
        print("Available commands:")
        print ("1. create restaurant")
        print ("2. delete restaurant")
        print ("3. update restaurant")
        print ("4. update user")
        print ("5. delete user")
        print ("6. create voucher")
        print ("7. update voucher")
        print ("8. delete voucher")
        print ("9. exit")

    def clientMenu(self):

        while(True):
            self.help_command_client()

            choice = input("Enter your choice: ")

            if choice == "1":
                status_code = self.register_user(self.username)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "2":
                status_code = self.delete_user(self.username)
                if status_code is not None:
                    print("Request status code:", status_code)
                    break
                else:
                    print("Failed to create request")
            if choice == "3":
                status_code = self.read_voucher(self.username)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "4":
                restaurantId = input("Enter the restaurant id: ")
                voucherCode = input("Enter the voucher code: ")
                description = input("Enter the description: ")
                status_code = self.create_review(self.username, restaurantId, voucherCode, description)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "5":
                status_code = self.read_review(self.username)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "6":
                restaurantId = input("Enter the restaurant id: ")
                voucherCode = input("Enter the voucher code: ")
                description = input("Enter the description: ")
                status_code = self.update_review(self.username, restaurantId, voucherCode, description)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "7":
                status_code = self.delete_review(self.username)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "8":
                break
            else:
                print("Invalid choice. Please try again.")

    def adminMenu(self):
        while(True):

            self.help_command_admin()

            choice = input("Enter your choice: ")

            if choice == "1":
                restaurantInfoPath = input("Enter the restaurant info path: ")
                status_code = self.create_restaurant(restaurantInfoPath)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "2":
                restaurantInfoId = input("Enter the restaurant info id: ")
                status_code = self.delete_restaurant(restaurantInfoId)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "3":
                restaurantInfoId = input("Enter the restaurant info id: ")
                restaurantInfoPath = input("Enter the restaurant info path: ")
                status_code = self.update_restaurant(restaurantInfoId, restaurantInfoPath)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "4":
                username = input("Enter the username: ")
                userNewName = input("Enter the new username: ")
                status_code = self.update_user(username, userNewName)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "5":
                username = input("Enter the username: ")
                status_code = self.delete_user(username)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "6": 
                username = input("Enter the username: ")
                restaurantId = input("Enter the restaurant id: ")
                voucherCode = input("Enter the voucher code: ")
                description = input("Enter the description: ")
                status_code = self.create_voucher(username, restaurantId, voucherCode, description)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "7":
                voucherId = input("Enter the voucher id: ")
                voucherCode = input("Enter the voucher code: ")
                description = input("Enter the description: ")
                status_code = self.update_voucher(voucherId, voucherCode, description)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "8":
                voucherId = input("Enter the voucher id: ")
                status_code = self.delete_voucher(voucherId)
                if status_code is not None:
                    print("Request status code:", status_code)
                else:
                    print("Failed to create request")
            if choice == "9":
                break
            else:
                print("Invalid choice. Please try again.")
    
    def registerLogic(self):
        self.register_user()
        if(self.username == "admin"):
            self.adminMenu()
        else:
            self.clientMenu()

    
    def loginLogic(self):
        self.login_user()
        if(self.username == "admin"):
            self.adminMenu()
        else:
            self.clientMenu()

    def InterfaceMenu(self):
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            self.loginLogic()
        elif choice == "2":
            self.registerLogic()
        elif choice == "3":
            exit()
        else:
            print("Invalid choice. Please try again.")
            self.InterfaceMenu()

   

if __name__ == "__main__":
    base_url = "https://192.168.2.0:5000/api"  # Replace with your actual base URL
    # Specify the path to your certificate file
    certificate_server_path = "certificate/certificate_server.pem"
    certificate_client_path = "certificate/cert.pem"
    key_path = "certificate/key.pem"
    username = input("Enter your username: ")
    client = ClientInterface(base_url, username, certificate_server_path, certificate_client_path, key_path)
    client.InterfaceMenu()

   
