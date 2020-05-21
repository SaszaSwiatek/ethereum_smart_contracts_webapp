from flask import session
import requests


class UserClient:

    @staticmethod
    def get_user(api_key):
        headers = {
            'Authorization': api_key
        }

        response = requests.request(method="GET", url='http://user:5000/api/user', headers=headers)
        if response.status_code == 401:
            return False

        user = response.json()
        return user
    
    @staticmethod
    def get_users():
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.request(method="GET", url='http://user:5000/api/users', headers=headers)
        users = response.json()
        return users
    
    @staticmethod
    def get_eth_prv_key(user_id):
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        url = 'http://user:5000/api/user/'+str(user_id)+'/eth_prv_key'
        response = requests.request(method="GET", url=url, headers=headers)
        eth_prv_key_resposne = response.json()
        return eth_prv_key_resposne