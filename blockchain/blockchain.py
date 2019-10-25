from flask import Flask, request, jsonify, render_template
from time import time
from flask_cors import CORS
from collections import OrderedDict

class Blockchain:

    def __init__(self):
        self.transactions = []
        self.chain = []
        # Create the genesis block
        self.create_block(0, '00')

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

    def submit_transaction(self, sender_public_key, recipient_public_key, signature, amount):
        # TODO : Reward the minor
        # TODO : Signature validation
        transaction = OrderedDict({
            'sender_public_key' : sender_public_key,
            'recipient_public_key' : recipient_public_key,
            'signature' : signature,
            'amount' : amount
        })
        signature_verification = True
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


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.form

    # Check the required field
    transaction_result = blockchain.submit_transaction(values['confirmation_sender_public_key'], values['confirmation_recipient_public_key'], values['transaction_signature'], values['confirmation_amount'])
    if transaction_result == False:
        response = {'message': 'Invalid Transaction'}
        return jsonify(response), 406
    else:
        response = {'message': 'Transaction will be added to the block' + str(transaction_result)}
        return jsonify(response), 201


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help="port to listen to")
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port, debug=True)
