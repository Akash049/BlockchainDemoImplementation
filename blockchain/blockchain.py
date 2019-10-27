from flask import Flask, request, jsonify, render_template
from time import time
from flask_cors import CORS
from collections import OrderedDict
import binascii
from Crypto.PublicKey import RSA
from collections import OrderedDict
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from uuid import uuid4
import json
import hashlib
import requests
from urllib.parse import urlparse

MINING_SENDER = 'The Blockchain'
MINING_REWARD = 1
MINING_DIFFICULTY = 2

class Blockchain:

    def __init__(self):
        self.transactions = []
        self.chain = []
        self.nodes = set()
        self.node_id = str(uuid4()).replace('-', '')
        # Create the genesis block
        self.create_block(0, '00')

    # Adding a new node to the chain
    def register_node(self, node_url):
        # Before adding the node, check if the url is valid or not
        parsed_url = urlparse(node_url)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    @staticmethod
    def valid_proof(transactions, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        guess = (str(transactions) + str(last_hash) + str(nonce)).encode('utf8')
        h = hashlib.new('sha256')
        h.update(guess)
        guess_hash = h.hexdigest()
        return guess_hash[:difficulty] == '0'*difficulty

    def proof_of_work(self):
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)
        nonce = 0
        while (self.valid_proof(self.transactions, last_hash, nonce)) is False:
            nonce += 1
        return nonce

    @staticmethod
    def hash(block):
        # Ensure that the dictionary is ordered to get the consistent hashes
        block_string = json.dumps(block, sort_keys=True).encode('utf8')
        h = hashlib.new('sha256')
        h.update(block_string)
        return h.hexdigest()

    # This is an important methods needed to be called before starting mining,
    # else mining will be done on wrong chain and proof of work will not be excepted
    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get('http://'+node+'/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Now, once we get the chain of other node check if chain is valid and longer that this node
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # After all the iteration, if we find that the other chain is valid and longer then use that chain
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def valid_chain(self, chain):
        # Now, to valid every block we need to validate every block
        # For this we iterate over the blocks and identify 2 things
        # 1). previous_hash of this block is same as the hash of the previous block
        # 2). The Nonce is actually valid and makes the right hash of given format

        # Current Index is 1 as the chain first chain is empty
        last_block = chain[0]
        current_index = 1

        # Iterate and compare the blocks
        while current_index < len(chain):
            block = chain[current_index]

            # Check if the previous hash of current block is same as the hash of the previous block
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Here we are getting the list of transactions to check for the nonce.
            # Except the last transaction that has the mined block data
            # coz that does not need to be validated
            transactions =  block['transactions'][:-1]
            transaction_elements = ['sender_public_key', 'recipient_public_key', 'amount']

            # Collect all transactions of a given block
            transactions = [OrderedDict((k, transaction[k]) for k in transaction_elements ) for transaction in transactions ]

            # Compare the validity if the nonce
            if not self.valid_proof(transactions, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
                return False

            last_block = block
            current_index += 1
        return True

    def create_block(self, nonce, previous_hash):
        """
        Add a block of transactions to the blockchain
        """
        block = {'block_number': len(self.chain) + 1,
                 'timestamp': time(),
                 'transactions': self.transactions,
                 'nonce': nonce,
                 'previous_hash': previous_hash}

        # Reset the current list of transactions
        self.transactions = []
        self.chain.append(block)
        return block

    @staticmethod
    def verify_transaction_signature(sender_public_key, signature, transaction):
        """
        :param sender_public_key:
        :param signature:
        :param transaction:
        :return:
        """
        public_key = RSA.importKey(binascii.unhexlify(sender_public_key))
        verifier = PKCS1_v1_5.new(public_key)
        transaction_hash = SHA.new(str(transaction).encode('utf8'))
        try:
            verifier.verify(transaction_hash, binascii.unhexlify(signature))
            return True
        except ValueError:
            return False

    def submit_transaction(self, sender_public_key, recipient_public_key, signature, amount):
        # TODO : Reward the minor
        # TODO : Signature validation
        transaction = OrderedDict({
            'sender_public_key': sender_public_key,
            'recipient_public_key': recipient_public_key,
            'amount': amount
        })

        # Reward for mining a block
        # If transaction is from a miner then no check is needed and can be directly appended
        if sender_public_key == MINING_SENDER:
            self.transactions.append(transaction)
            return len(self.chain) + 1
        else:
            # Transaction from one wallet to another wallet
            # if transaction if from a non-miner then since it is a chain, thus it needs to be verified first
            signature_verification = self.verify_transaction_signature(sender_public_key, signature, transaction)
            if signature_verification:
                self.transactions.append(transaction)
                return len(self.chain) + 1
            else:
                return False


# Instantiate the Blockchain
blockchain = Blockchain()

# Instantiate the Node
app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return render_template('./index.html')

@app.route('/configure')
def configure():
    return render_template('./configure.html')

@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    transactions = blockchain.transactions
    response = {'transactions': transactions}
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/mine', methods=['GET'])
def mine():
    # First find the none, which shows the proof of work
    # We run the proof of work algorithm
    nonce = blockchain.proof_of_work()

    blockchain.submit_transaction(sender_public_key=MINING_SENDER,
                                  recipient_public_key=blockchain.node_id,
                                  signature='',
                                  amount=MINING_REWARD)
    last_block = blockchain.chain[-1]
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(nonce, previous_hash)
    response = {
        'message': 'New block created',
        'block_number': block['block_number'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.form

    # Check all the required field
    required = ['confirmation_sender_public_key', 'confirmation_recipient_public_key', 'transaction_signature', 'confirmation_amount']
    if not all(k in values for k in required):
        return 'Missing Values', 400

    # Check the required field
    transaction_result = blockchain.submit_transaction(
            values['confirmation_sender_public_key'],
            values['confirmation_recipient_public_key'],
            values['transaction_signature'],
            values['confirmation_amount'])
    if not transaction_result:
        response = {'message': 'Invalid Transaction'}
        return jsonify(response), 406
    else:
        response = {'message': 'Transaction will be added to the block' + str(transaction_result)}
        return jsonify(response), 201

@app.route('/nodes/get', methods=['GET'])
def get_nodes():
    nodes = list(blockchain.nodes)
    response = {'nodes': nodes}
    return jsonify(response), 200

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_node():
    values = request.form
    nodes = values.get('nodes').replace(' ', '').split(',')

    if nodes is None:
        return 'Error: Please supply a valid list of node', 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Nodes have been added',
        'total_nodes': [node for node in blockchain.nodes]
    }
    return jsonify(response), 200

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help="port to listen to")
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port, debug=True)
