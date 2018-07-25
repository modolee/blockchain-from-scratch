from hashlib import sha256
import json
import time

from flask import Flask, request
import requests

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index  # 블록 번호
        self.transactions = transactions  # 트랜잭션
        self.timestamp = timestamp  # 타임 스탬프
        self.previous_hash = previous_hash  # 이전 블록 해시
        self.nonce = 0  # 논스

    def compute_hash(self):
        """
        블록의 정보를 16진수 Hash로 만드는 함수
        :return: 블록 정보 해시 256 bits (32 bytes)

        * 블록 정보 예시 :
        {"index": 0, "nonce":"0", "previous_hash": "0", "timestamp": 1532487065.7013392, "transactions": []}
        * 블록 해시 예시 :
        7b7cca5efcab11076001d2eb6d3087af073a7c836eeda5f72c8bfbded134d5b6
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 2  # PoW 알고리즘의 채굴 난이도

    def __init__(self):
        self.unconfirmed_transactions = []  # 채굴 안 된(pending) 트랜잭션들
        self.chain = []  # 블록 체인 (리스트)
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Genesis block을 만들고 blockchain에 추가하는 함수
        """
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    def proof_of_work(self, block):
        """
        채굴 난이도(difficulty)에 만족하는 nonce를 찾는 함수
        :param block: nonce를 찾기 위한 블록
        :return: 채굴 난이도에 만족하는 nonce를 포함하는 블록 해시
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_block(self, block, proof):
        """
        블록 검증 후에 블록을 블록체인에 추가 하는 함수
        :param block: 블록체인에 추가 할 블록
        :param proof: PoW로 찾은 블록 해시
        :return: 블록이 유효 한 경우 True / 그렇지 않으면 False
        """
        previous_hash = self.last_block.hash

        # 체인에 등록 된 이전 블록 해시와
        # 새롭게 추가하려는 블록의 이전 블록 해시가 다른 경우
        if previous_hash != block.previous_hash:
            return False

        # 채굴 난이도에 알맞은 블록 해시 값이 아닌 경우
        if not self.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        """
        채굴 난이도에 만족하는 블록 해시인지,
        블록 정보를 해시한 값과 블록 해시가
        일치하는 지 확인하는 함수
        :param block: 검증하려는 블록
        :param block_hash: 검증하려는 블록 해시
        :return: 참 / 거짓
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        """
        아직 블록 체인에 연결되지 않은(pending) 트랜잭션을
        블록에 포함하고 nonce를 찾아내는 PoW를 수행하여
        유효한 블록을 생성하고 블록체인에 연결하는 함수
        :return:
            * pending 트랜잭션이 없는 경우 :  False
            * 유효한 블록을 생성한 경우 : 새로 생성 되어 블록체인에 연결 된 블록의 블록 번호
        """
        # pending 트랜잭션이 없는 경우
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,  # 트랜잭션 개수 제한은 없음
                          timestamp=time.time(),
                          previous_hash=last_block.hash)
        proof = self.proof_of_work(new_block)  # nonce 값을 찾고
        self.add_block(new_block, proof)  # 블록체인에 연결
        self.unconfirmed_transactions = []  #pending 트랜잭션 초기화
        return new_block.index

    @property
    def last_block(self):
        return self.chain[-1]


app = Flask(__name__)

blockchain = Blockchain()

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()
    blockchain.add_new_transaction(tx_data)

    return "Success", 201

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dump({"length": len(chain_data),
                      "chain": chain_data})

@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined.".format(result)

@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)

app.run(debug=True, host='0.0.0.0', port=7000)