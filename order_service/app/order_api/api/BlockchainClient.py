import requests
from web3 import Web3
class BlockchainClient:

    @staticmethod
    def get_eth_balance(eth_address):
        web3 = Web3(Web3.HTTPProvider('http://ganache:8545'))
        if not web3.isConnected():
          return {'message': 'Blockchain provider not connected'}
        balance = web3.eth.getBalance(eth_address)
        balance_formated = web3.fromWei(balance, "ether")
        return {'message': 'success', 'eth_address': eth_address, 'eth_balance': balance_formated}


    #@staticmethod
    #def send_transfer(eth_sender_address,eth_recipient_address,value,eth_prv_key):
    #    web3 = Web3(Web3.HTTPProvider('http://ganache:8545'))
    #    if not web3.isConnected():
    #        return {'message': 'Blockchain provider not connected'}
    #    signed_txn = web3.eth.account.signTransaction(dict(nonce=web3.eth.getTransactionCount(eth_sender_address),gasPrice = web3.eth.gasPrice, gas = 100000,to=eth_recipient_address,value=web3.toWei(value,'ether')),eth_prv_key)
    #    transactionhash = web3.eth.sendRawTransaction(signed_txn.rawTransaction).hex()
    #    return {'message': "success transaction has been done, transaction hash - "+str(transactionhash), 'transactionhash': transactionhash}