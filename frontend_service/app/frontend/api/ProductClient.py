from flask import session
import requests


class ProductClient:

    @staticmethod
    def get_product(slug):
        response = requests.request(method="GET", url='http://product:5000/api/product/' + slug)
        product = response.json()
        return product

    @staticmethod
    def get_products():
        r = requests.get('http://product:5000/api/products')
        products = r.json()
        return products

    @staticmethod
    def get_user_contracts():
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        url = 'http://product:5000/api/contracts'
        response = requests.request("GET",url=url,headers=headers)
        contracts = response.json()
        return contracts

    @staticmethod
    def does_contract_title_exists(contract_title):
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        url = 'http://product:5000/api/contract/'+contract_title+'/exists'
        response = requests.request("GET", url=url, headers=headers)
        return response.status_code == 200

    @staticmethod
    def post_add_contract(form):
        payload = {
            'title': form.title.data,
            'content': form.content.data,
            'contractor_user_id': form.contractor_user_id.data,
            'contract_template_id': form.contract_template_id.data,
            'value': form.value.data,
            'duedate': form.duedate.data
        }
        url = 'http://product:5000/api/add-contract'
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.request("POST", url=url, data=payload, headers=headers)
        if response:
            contract = response.json()
            return contract

    @staticmethod
    def get_contract(contract_id):
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.request(method="GET", url='http://product:5000/api/contract/' + contract_id, headers=headers)
        product = response.json()
        return product

        
    @staticmethod
    def post_delete_contract(contract_id):
        url = 'http://product:5000/api/contract/'+str(contract_id)+'/delete'
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.request("POST", url=url, headers=headers)
        if response:
            contract = response.json()
            return contract

    @staticmethod
    def post_add_attachment(form):
        payload = {
            'name': form.name.data,
            'filename': form.filename.data,
            'contract_id': form.contract_id.data,
            'description': form.description.data
        }
        url = 'http://product:5000/api/add_attachment'
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.request("POST", url=url, data=payload, headers=headers)
        json_response = response.json()
        if json_response['message'] == 'success':
            return json_response