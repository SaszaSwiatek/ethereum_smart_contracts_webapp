from flask import session
import requests


class ProductClient:

    @staticmethod
    def get_contract(contract_id):
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.request(method="GET", url='http://product:5000/api/contract/' + contract_id, headers=headers)
        product = response.json()
        return product
    
    @staticmethod
    def contract_set_as_deployed(contract_id,contractAddress):
        payload = {
            'contractAddress': contractAddress,
            'contract_id': contract_id
        }
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        url = 'http://product:5000/api/contract/'+ contract_id +'/contract_set_as_deployed'
        response = requests.request("POST", url=url, data=payload, headers=headers)
        some_variable = response.json()
        if some_variable['message'] == 'success':
            return some_variable
   
    @staticmethod
    def contract_set_as_finalized(contract_id):
        payload = {
            'contract_id': contract_id,
            'it_needs_second_var': contract_id
        }
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        url = 'http://product:5000/api/contract/'+ contract_id +'/contract_set_as_finalized'
        response = requests.request("POST", url=url, data=payload, headers=headers)
        some_variable = response.json()
        if some_variable['message'] == 'success':
            return some_variable