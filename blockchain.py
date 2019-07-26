import random
from time import time
from wallet import sha_256, get_address, sign, verify_sign, _r
import requests
from merkle import merkle_tree
import json

DIFFICULTY = 2


class Blockchain:
    def __init__(self):
        self.private_key = random.randint(1, _r)
        self.public_key, self.address = get_address(self.private_key)
        self.amount = 0     # 初始化账户余额
        #  public_key转化为str，需要转化回来为元组
        self.current_transactions = []  # 自己的交易池
        self.receive_transactions = []  # 别人的交易池
        self.chain = []
        self.genesis_block()

        self.neighbor = set()  # 邻居节点
        print('输入节点ip:port')  #第一个客户端固定为'127.0.0.1:5000'
        self.ip = ""

        #  初始化coin_base奖励
        self.mine_transaction = {'amount': 50, 'recipient': str(self.public_key), 'sender': 'Satoshi'}
        self.coin_base = [[self.mine_transaction, {'txhash': sha_256(self.mine_transaction)}]]
        self.msg = []

    def genesis_block(self):
        block = {
            'index': 0,
            'merkle_tree': '000000',
            'previous_hash': '000000',
            'proof': 138,
            'timestamp': 1559273178.3706222,
            'transactions': [],
        }
        self.chain.append(block)

    def proof_of_work(self):
        # coin_base交易结构[[{tx},{txhash}]]
        proof = 0
        t = time()
        mk = [self.coin_base[0][1]['txhash']]
        for tx in self.current_transactions:
            mk.append(tx[2]['txhash'])
        block = {
            'index': len(self.chain),
            'merkle_tree': merkle_tree(mk),
            'previous_hash': sha_256(self.chain[-1]),
            'proof': proof,
            'timestamp': t,
            'transactions': self.coin_base + self.current_transactions + self.receive_transactions,
        }
        while self.valid_proof(block) is False:
            proof += 1
            block['proof'] = proof
        self.current_transactions = []
        self.receive_transactions = []
        self.chain.append(block)
        self.utxo_pool(block)
        return block

    @staticmethod
    def valid_proof(block, difficulity=DIFFICULTY):
        guess_hash = sha_256(block)
        return guess_hash[:difficulity] == "0"*difficulity

    def sub_transaction(self, recipient, amount):
        # 交易结构[[t1,t2,t3]]
        if amount > self.amount:
            return False
        else:
            t1 = {# 字典顺序不能修改，否则网络传输过程中改变最终hash值
                    'amount': amount,
                    'recipient': recipient,
                    'sender': str(self.public_key),
                    }
            signature = sign(t1, self.private_key)
            t2 = {'signature': signature}
            t3 = {'txhash': sha_256(t1)}
            tx = [t1, t2, t3]
            self.current_transactions.append(tx)
            return True

    # 账户是否有足够的钱
    def utxo_pool(self, block):
        # 交易提交之前检验余额是否足够
        if block['transactions'][0][0]['recipient'] == str(self.public_key):
            self.amount = self.amount + 50
        for tx in block['transactions'][1:]:
            if tx[0]['sender'] == str(self.public_key):
                self.amount = self.amount - tx[0]['amount']

            if tx[0]['recipient'] == str(self.public_key):
                self.amount = self.amount + tx[0]['amount']

    def resolve_conflicts(self):
        new_chain = None
        max_length = len(self.chain)
        if len(self.neighbor) == 0:
            pass
        else:
            for node in self.neighbor:
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Check if the length is longer and the chain is valid
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
        if new_chain:
            self.chain = new_chain
            self.amount = 0
            for block in self.chain[1:]:
                self.utxo_pool(block)
            self.current_transactions = []
            self.receive_transactions = []
            return True
        return False

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            last_block_hash = sha_256(last_block)
            if block['previous_hash'] != last_block_hash:
                self.msg.append('hash wrong')
                return False
            if not self.valid_proof(block):
                self.msg.append('proof wrong')
                return False
            if not self.valid_block_transaction(block):
                self.msg.append('t wrong')
                return False
            last_block = block
            current_index += 1
        return True

    @staticmethod
    def valid_block_transaction(block):
        transactions = block['transactions'][1:]
        if len(transactions) == 0:
            return True
        else:
            for tx in transactions:
                if not (verify_sign(tx[0], eval(tx[0]['sender']), tx[1]['signature'])):
                    return False
            return True


if __name__ == '__main__':
    b = Blockchain()
    b.sub_transaction('123', 29)
    b.proof_of_work()
    print(b.amount)
    b.sub_transaction('123', 22)
    b.proof_of_work()
    print(b.amount)
    b.sub_transaction('123', 13)
    b.proof_of_work()
    print(b.amount)
    c = b.chain
    d = b.valid_chain(c)
    print(d)