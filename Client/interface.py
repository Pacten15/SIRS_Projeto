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
            status_code = response.status_code
            return [data, status_code]
        except requests.exceptions.HTTPError as errh:
            print ("Http Error:",errh)
        except requests.exceptions.ConnectionError as errc:
            print ("Error Connecting:",errc)
        except requests.exceptions.Timeout as errt:
            print ("Timeout Error:",errt)
        except requests.exceptions.RequestException as err:
            print ("Something went wrong with the request:",err)
    
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
        if response[1] == 201:
            print("User created successfully.")
        elif response[1] == 400:
            # Extract the content from the data dictionary
            content_json = json.loads(response[0]['content'])
            # Access the 'error' field within the 'json' key
            error_message = content_json['json']['error']
            print(error_message)
        
        
    
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
        if response[1] == 200:
            print("User logged in successfully.")
        else:
            # Extract the content from the data dictionary
            content_json = json.loads(response[0]['content'])
            # Access the 'error' field within the 'json' key
            error_message = content_json['json']['error']
            print(error_message)
        

    def update_user(self):
        keys = BA.create_key_pair(2048, 'keys/' + self.username + '.pubkey', 'keys/' + self.username + '.privkey')
        public_key = keys[0]
        private_key = keys[1]
        update_json = {
            'user_name': self.username,
            'public_key': public_key.decode(),
            'operation': 'update'
        }

        private_key_old = BA.str_to_key(self.privkey.decode())
        data = BA.encrypt_json(update_json, private_key_old, None) 
        response= https_post_requests(self.base_url + '/users', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        if response[1] == 200:
            self.privkey = private_key
            self.pubkey = public_key
            print("User updated successfully.")
        elif response[1] == 400:
            # Extract the content from the data dictionary
            content_json = json.loads(response[0]['content'])
            # Access the 'error' field within the 'json' key
            error_message = content_json['json']['error']
            print(error_message)
    
    def read_user(self, username):
        read_json = {
            'user_name': self.username,
            'user_name_to_read': username,
            'operation': 'read'
        }
        private_key = BA.str_to_key(self.privkey.decode())
        data = BA.encrypt_json(read_json, private_key, None)
        response = https_post_requests(self.base_url + '/users', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        if response[1] == 200:
            content_json = json.loads(response[0]['content'])
            print("User: " + username + "\nPublic key: " + content_json['json']['public_key'] + "\n")
        else:
            # Extract the content from the data dictionary
            content_json = json.loads(response[0]['content'])
            # Access the 'error' field within the 'json' key
            error_message = content_json['json']['error']
            print(error_message)
        
    
    def list_all_users(self):
        list_users= {
            'user_name': self.username,
            'operation': 'list'
        }

        private_key = BA.str_to_key(self.privkey.decode())
        data = BA.encrypt_json(list_users, private_key, None)
        response = https_post_requests(self.base_url + '/users', data, self.certificate_client_path, self.key_path, self.certificate_server_path)

        if response[1] == 200:
            content_json = json.loads(response[0]['content'])
            users = content_json['json']['users']
            for user in users:
                print("User: " + user['name'] + "\nPublic key: " + user['public_key'] + "\n")



      
    def delete_user(self, username):
        delete_json = {
            'user_name': self.username,
            'user_name_to_delete': username,
            'operation': 'delete'
        }
        private_key = BA.str_to_key(self.privkey.decode())
        data = BA.encrypt_json(delete_json, private_key, None)
        response = https_post_requests(self.base_url + '/users', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        os.remove('keys/' + username + '.pubkey')
        os.remove('keys/' + username + '.privkey')
        if response[1] == 200:
               print("User deleted successfully.")
        else:
            # Extract the content from the data dictionary
            content_json = json.loads(response[0]['content'])
            # Access the 'error' field within the 'json' key
            error_message = content_json['json']['error']
            print(error_message)

      
    def create_restaurant(self, restaurantInfoPath):
        
        restaurantInfo = read_json_file(restaurantInfoPath)
        createRestaurant = {
            'user_name': self.username,
            'data': restaurantInfo
        }
        private_key = BA.str_to_key(self.privkey.decode())
        data = BA.encrypt_json(createRestaurant, private_key, None)
        response = https_post_requests(self.base_url + '/restaurant', data, self.certificate_client_path, self.key_path, self.certificate_server_path)
        
    
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
        print("1.  delete self")
        print("2.  update self keys")
        print("3.  list restaurants")
        print("4.  read restaurant")
        print("5.  list vouchers")
        print("6.  transfer voucher")
        print("7.  redeem voucher")
        print("8.  write review")
        print("9.  read own reviews")
        print("10. update review")
        print("11. delete review")
        print("12. exit")
    
    def help_command_admin(self):
        print("Available commands:")
        print("1.  list users")
        print("2.  delete user")
        print("3.  update admin keys")
        print("4.  create restaurant")
        print("5.  list restaurants")
        print("6.  read restaurant")
        print("7.  delete restaurant")
        print("8.  create voucher")
        print("9.  exit")

    def clientMenu(self):

        while(True):
            self.help_command_client()

            choice = input("Enter your choice: ")

            if choice == "1":
                self.delete_user(self.username)
                break

            elif choice == "2":
                self.update_user()

            elif choice == "12":
                break
            else:
                print("Invalid choice. Please try again.")

    def adminMenu(self):
        while(True):

            self.help_command_admin()

            choice = input("Enter your choice: ")

            if choice == "1":
                usernameToRead = input("Enter the username to read: ")
                usernameToRead = ''.join(usernameToRead)
                self.read_user(usernameToRead)

            elif choice == "2":
                self.list_all_users()

            elif choice == "10":
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
        if(os.path.isfile('keys/' + self.username + '.pubkey') and os.path.isfile('keys/' + self.username + '.privkey')):
            self.login_user()
            if(self.username == "admin"):
                self.adminMenu()
            else:
                self.clientMenu()
        else:
            print("User not registered. Please register first.")
            self.InterfaceMenu()

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

   
