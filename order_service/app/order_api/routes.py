from flask import jsonify,json, request, make_response, session
from . import order_api_blueprint
from models import db, Order, OrderItem
from .api.UserClient import UserClient
from .api.ProductClient import ProductClient
from .api.BlockchainClient import BlockchainClient
from web3 import Web3
import json

@order_api_blueprint.route("/api/order/docs.json", methods=['GET'])
def swagger_api_docs_yml():
    with open('swagger.json') as fd:
        json_data = json.load(fd)

    return jsonify(json_data)


@order_api_blueprint.route('/api/orders', methods=['GET'])
def orders():

    items = []
    for row in Order.query.all():
        items.append(row.to_json())

    response = jsonify(items)

    return response


@order_api_blueprint.route('/api/order/add-item', methods=['POST'])
def order_add_item():

    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']

    p_id = int(request.form['product_id'])
    qty = int(request.form['qty'])
    u_id = int(user['id'])

    # Find open order
    known_order = Order.query.filter_by(user_id=u_id, is_open=1).first()

    if known_order is None:
        # Create the order
        known_order = Order()
        known_order.is_open = True
        known_order.user_id = u_id

        order_item = OrderItem(p_id, qty)
        known_order.items.append(order_item)

    else:
        found = False
        # Check if we already have an order item with that product
        for item in known_order.items:

            if item.product_id == p_id:
                found = True
                item.quantity += qty

        if found is False:
            order_item = OrderItem(p_id, qty)
            known_order.items.append(order_item)

    db.session.add(known_order)
    db.session.commit()

    response = jsonify({'result': known_order.to_json()})

    return response


@order_api_blueprint.route('/api/order', methods=['GET'])
def order():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']

    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()

    if open_order is None:
        response = jsonify({'message': 'No order found'})
    else:
        response = jsonify({'result': open_order.to_json()})

    return response


@order_api_blueprint.route('/api/order/checkout', methods=['POST'])
def checkout():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']

    order_model = Order.query.filter_by(user_id=user['id'], is_open=1).first()
    order_model.is_open = 0

    db.session.add(order_model)
    db.session.commit()

    response = jsonify({'result': order_model.to_json()})

    return response

@order_api_blueprint.route('/api/contract/<contract_id>/deploy', methods=['POST'])
def deploy_contract(contract_id):
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 200)
    session['user_api_key'] = response['result']['api_key']

    current_user = response
    response_contract = ProductClient.get_contract(contract_id)
    if response_contract['message'] != 'success':
        return make_response(jsonify({'message': 'Contract not found'}), 200)

    if current_user['result']['id'] != response_contract['result']['contractor_user_id'] or response_contract['result']['contractor_approval'] == True:
        return make_response(jsonify({'message': 'You are not authorized for deploying that contract'}), 200)

    eth_prv_key_resposne = UserClient.get_eth_prv_key(response_contract['result']['user_id'])
    if eth_prv_key_resposne['message'] != 'success':
        return make_response(jsonify({'message': 'Could not reach initiators wallet'}), 200)
    #initiator_eth_prv_key = eth_prv_key_resposne['result']['eth_prv_key']
    #initiator_eth_address = eth_prv_key_resposne['result']['eth_address']
    #current_user['result']['eth_address']
    return_initiator_eth_balance = BlockchainClient.get_eth_balance(eth_prv_key_resposne['result']['eth_address'])
    if return_initiator_eth_balance['message'] != 'success':
        return make_response(jsonify({'message': 'Could not read check initiator balance'}), 200)
    #initiator_eth_balance = return_initiator_eth_balance['eth_balance']

    if int(response_contract['result']['value']) > return_initiator_eth_balance['eth_balance']:
        return make_response(jsonify({'message': 'Initiators balance is lower than contract value'}), 200)

    w3 = Web3(Web3.HTTPProvider("http://ganache:8545"))
    if not w3.isConnected():
        return make_response(jsonify({'message': 'Could not connect to blockchain'}), 200)
    
    abi = json.loads('[{"inputs":[{"internalType":"address payable","name":"_contractor","type":"address"},{"internalType":"uint256","name":"_releaseTime","type":"uint256"}],"payable":true,"stateMutability":"payable","type":"constructor"},{"constant":true,"inputs":[],"name":"contract_value","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"contractor","outputs":[{"internalType":"address payable","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"finalize","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"initiator","outputs":[{"internalType":"address payable","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"releaseTime","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]')
    bytecode = "608060405260405161078c38038061078c8339818101604052604081101561002657600080fd5b810190808051906020019092919080519060200190929190505050336000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff1602179055503460028190555042811161009457600080fd5b81600160006101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff1602179055508060038190555060006060600160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff166064600a606e6064600254028161012c57fe5b04028161013557fe5b0460405180600001905060006040518083038185875af1925050503d806000811461017c576040519150601f19603f3d011682016040523d82523d6000602084013e610181565b606091505b5091509150816101f9576040517f08c379a00000000000000000000000000000000000000000000000000000000081526004018080602001828103825260208152602001807f4661696c656420746f2073656e642031302520616476616e636520457468657281525060200191505060405180910390fd5b505050506105808061020c6000396000f3fe608060405234801561001057600080fd5b50600436106100575760003560e01c80634bb278f31461005c5780635c39fcc114610066578063b91d4001146100b0578063e354d517146100ce578063fbfd2045146100ec575b600080fd5b610064610136565b005b61006e61046d565b604051808273ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200191505060405180910390f35b6100b8610492565b6040518082815260200191505060405180910390f35b6100d6610498565b6040518082815260200191505060405180910390f35b6100f461049e565b604051808273ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200191505060405180910390f35b6000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff161461018f57600080fd5b60035442116102835760006060600160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff164760405180600001905060006040518083038185875af1925050503d806000811461021c576040519150601f19603f3d011682016040523d82523d6000602084013e610221565b606091505b50915091508161027c576040517f08c379a00000000000000000000000000000000000000000000000000000000081526004018080602001828103825260368152602001806104f06036913960400191505060405180910390fd5b505061046b565b60006060600160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff166064605a606e606460025402816102d357fe5b0402816102dc57fe5b0460405180600001905060006040518083038185875af1925050503d8060008114610323576040519150601f19603f3d011682016040523d82523d6000602084013e610328565b606091505b509150915081610383576040517f08c379a00000000000000000000000000000000000000000000000000000000081526004018080602001828103825260268152602001806105266026913960400191505060405180910390fd5b600060606000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff164760405180600001905060006040518083038185875af1925050503d8060008114610406576040519150601f19603f3d011682016040523d82523d6000602084013e61040b565b606091505b509150915081610466576040517f08c379a000000000000000000000000000000000000000000000000000000000815260040180806020018281038252602b8152602001806104c5602b913960400191505060405180910390fd5b505050505b565b6000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b60035481565b60025481565b600160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff168156fe4661696c656420746f2073656e642072656d61696e696e6720457468657220746f20696e69746961746f724661696c656420746f2073656e642077686f6c6520636f6e726163742076616c756520457468657220746f20636f6e74726163746f724661696c656420746f2073656e642039302520457468657220746f20636f6e74726163746f72a265627a7a72315820fd10fe1695c92b77942711fc7e91b947c07173d90535b78ace017dce9b33db2464736f6c63430005110032"
    contract_ = w3.eth.contract(abi=abi,bytecode=bytecode)
    privateKey = eth_prv_key_resposne['result']['eth_prv_key']#"0x963c3038a3bf70188e1b900f5ea3f75b675200d5cd09e6a37c726c0be3cd3a7b"
    acct = w3.eth.account.privateKeyToAccount(privateKey)

    construct_txn = contract_.constructor(current_user['result']['eth_address'],int(response_contract['result']['duedate'])).buildTransaction({
       'from': acct.address,
       'nonce': w3.eth.getTransactionCount(acct.address),
       'gas': 1728712,
       'value' : w3.toWei(str(response_contract['result']['value']), 'ether'),
       'gasPrice': w3.toWei('21', 'gwei')
    })

    signed = acct.signTransaction(construct_txn)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    #print("transaction hash hex ",tx_hash.hex())
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    contract_address = tx_receipt.contractAddress
    if contract_address:
        ProductClient.contract_set_as_deployed(contract_id,tx_receipt.contractAddress)
    #print("tx_receipt= ",tx_receipt)
    #print("tx_contract_address= ",tx_receipt.contractAddress)
   
    return make_response(jsonify({'message': 'success','tx_receipt': contract_address}), 200)

@order_api_blueprint.route('/api/contract/<contract_id>/finalize', methods=['POST'])
def finalize_contract(contract_id):
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 200)
    session['user_api_key'] = response['result']['api_key']

    current_user = response
    response_contract = ProductClient.get_contract(contract_id)
    if response_contract['message'] != 'success':
        return make_response(jsonify({'message': 'Contract not found'}), 200)

    if current_user['result']['id'] != response_contract['result']['user_id'] and response_contract['result']['contractor_approval'] == True:
        return make_response(jsonify({'message': 'You are not authorized for finalizing that contract'}), 200)
    w3 = Web3(Web3.HTTPProvider("http://ganache:8545"))

    abi = json.loads('[{"inputs":[{"internalType":"address payable","name":"_contractor","type":"address"},{"internalType":"uint256","name":"_releaseTime","type":"uint256"}],"payable":true,"stateMutability":"payable","type":"constructor"},{"constant":true,"inputs":[],"name":"contract_value","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"contractor","outputs":[{"internalType":"address payable","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"finalize","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"initiator","outputs":[{"internalType":"address payable","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"releaseTime","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]')
    privateKey = current_user['result']['eth_prv_key']#"0x963c3038a3bf70188e1b900f5ea3f75b675200d5cd09e6a37c726c0be3cd3a7b"
    tx_contract_address = response_contract['result']['transaction_hash']
    contract_instance_for_calling = w3.eth.contract(
        address=tx_contract_address,
        abi=abi
    )
    acct = w3.eth.account.privateKeyToAccount(privateKey)
    transaction = contract_instance_for_calling.functions.finalize().buildTransaction({
        'gas': 70000,
        'gasPrice': w3.toWei('1', 'gwei'),
        'from': acct.address,
        'nonce': w3.eth.getTransactionCount(acct.address)
    }) 
    signed_txn = w3.eth.account.signTransaction(transaction, private_key=privateKey)
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

    transaction_hash_hex = tx_hash.hex()
    if transaction_hash_hex:
        ProductClient.contract_set_as_finalized(contract_id)
   
    return make_response(jsonify({'message': 'success','tx_receipt': transaction_hash_hex}), 200)