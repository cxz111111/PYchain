import requests
from flask import Flask, jsonify, request, render_template
from blockchain import Blockchain
import webbrowser
ROOT = '127.0.0.1:5000'

app = Flask(__name__)

blockchain = Blockchain()   # 实例化类
blockchain.ip = input()


@app.route('/', methods=['GET'])
def web_index():
    return render_template('index.html', chain=blockchain.chain)


@app.route('/wallet', methods=['GET'])
def wallet():
    pubk = str(blockchain.public_key)
    sk = str(blockchain.private_key)
    amount = blockchain.amount
    return render_template('index2.html', pubk=pubk, sk=sk, amount=amount)


# 交互返回界面类
@app.route('/get_map', methods=['GET'])
def get_map():
    if blockchain.ip == ROOT:
        log = '这是根节点'
    else:
        blockchain.neighbor.add(ROOT)
        resp = requests.get(f'http://{ROOT}/net_work')
        r = set(resp.json()['node_list'])
        r.remove(blockchain.ip)
        blockchain.neighbor.update(r)
        log = '节点更新成功'
    return render_template('index.html', log=log, chain=blockchain.chain)


@app.route('/receive_transaction', methods=['GET'])
def receive_transaction():
    if len(blockchain.neighbor) == 0:
        return render_template('index.html', log='没有新节点', chain=blockchain.chain)
    else:
        for i in blockchain.neighbor:
            resp = requests.get(f'http://{i}/transaction_pool')
            if resp.status_code == 200:
                blockchain.receive_transactions = resp.json()
        log = {'transaction': blockchain.receive_transactions}
        return render_template('index.html', log=log, chain=blockchain.chain)


@app.route('/consensus', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if len(blockchain.msg) != 0:
        log = blockchain.msg.pop()
    else:
        if replaced:
            log = {
                'message': '当前链被替换',
            }
        else:
            log = {
                'message': '当前链已经是最长的了',
            }
    return render_template('index.html', log=log, chain=blockchain.chain)


# 操作返回界面类
@app.route('/mine', methods=['GET'])
def mine():
    blockchain.proof_of_work()
    return render_template('index.html', log=blockchain.chain[-1], chain=blockchain.chain)


@app.route('/transaction', methods=['POST'])  # 自身交易池
def transaction():
    values = request.form
    values.to_dict()
    print(values)
    if values['recipient'] == '' or values['amount'] == '':
        return render_template('index.html', log='缺少值', chain=blockchain.chain)
    else:
        if blockchain.sub_transaction(values['recipient'], int(values['amount'])):
            log = blockchain.current_transactions
            return render_template('index.html', log=log, chain=blockchain.chain)
        else:
            return render_template('index.html', log='余额不足，请挖矿！', chain=blockchain.chain)


@app.route('/register_nodes', methods=['POST'])
def register_nodes():
    values = request.form
    values.to_dict
    n = values['node']
    if n is None:
        return render_template('index.html', log='请提供一个正确的ip', chain=blockchain.chain)
    else:
        blockchain.neighbor.add(n)
        log = {
            '新节点注册成功'
            '邻居节点': list(blockchain.neighbor),
        }
        return render_template('index.html', log=log, chain=blockchain.chain)


# 展示界面类
@app.route('/show_network', methods=['GET'])
def show_network():
    a = list(blockchain.neighbor)
    a.append(blockchain.ip)
    log = {
        '节点列表': a,
        '节点数量': len(a),
        }
    return render_template('index.html', log=log, chain=blockchain.chain)


@app.route('/show_transaction', methods=['GET'])
def show_transaction():
    return render_template('index.html', log=blockchain.current_transactions, chain=blockchain.chain)


# 接口类
@app.route('/net_work', methods=['GET'])
def net_work():
    a = list(blockchain.neighbor)
    a.append(blockchain.ip)
    response = {
        'node_list': a,
        'node_number': len(a), }
    return jsonify(response), 200


@app.route('/transaction_pool', methods=['GET'])
def transaction_pool():
    return jsonify(blockchain.current_transactions)


@app.route('/chain', methods=['GET'])
def chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

host = blockchain.ip.split(':')[0]
port = blockchain.ip.split(':')[1]
webbrowser.open('http://' + blockchain.ip)
app.run(host=host, port=int(port))


