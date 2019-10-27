# Block chain demo implementation
## Description
This project described a simple implementation of blockchain with following functionalities.
* Adding users to the blockchain node by generating public and private key.
* Providing and interface to generate transactions.
* Runnning multiple node servers inorder to keep a track of the transaction flow and also testing the conflict resolving between multiple node.
* Validating the transaction by signature validation.
* Mining the block and adding the transaction.

## Development
* The server side development is done in Flask(Python)
* The Front-end development is in plain JS and Bootstrap

## Process
* There are 5 servers in this app: 3 node servers and 2 client servers
* Run all the 5 servers together
* For every node add the address of the other 2 nodes using configure on the tab, in order to let each server know about the transaction added.
* Use the client side dashboard to generate the keys and then send the transaction to the other user.
* From any of the node server we can check the added transaction and then mine the block to add the transaction to the chain.
* Once added, move to any other servers and use refresh transaction to resolve any conflicts and add the mined transactions to all the servers.


