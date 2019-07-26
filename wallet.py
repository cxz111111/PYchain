import hashlib
import random
import json

_a = 0x0000000000000000000000000000000000000000000000000000000000000000
_b = 0x0000000000000000000000000000000000000000000000000000000000000007
_Gx = 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
G_point = (_Gx, _Gy)
_p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
_r = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
# 随机生成sk = random.randint(1, _r)或自己设置
sk = 123456
# h要转化为数字形式
h = 'dhsjdhsjdh'


def Mod_inv(a, n=_p):
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        ratio = high // low
        nm, new = hm - lm * ratio, high - low * ratio
        lm, low, hm, high = nm, new, lm, low
    return lm % n


def E_add(p, q):
    lam = ((q[1] - p[1]) * Mod_inv(q[0] - p[0], _p)) % _p
    rx = (lam * lam - p[0] - q[0]) % _p
    ry = (lam * (p[0] - rx) - p[1]) % _p
    return rx, ry


def E_double(p):
    lam = ((3 * p[0] * p[0] + _a) * Mod_inv((2 * p[1]), _p)) % _p
    rx = (lam * lam - 2 * p[0]) % _p
    ry = (lam * (p[0] - rx) - p[1]) % _p
    return rx, ry


def Emultiply(point, secret_key):
    if secret_key == 0 or secret_key >= _r:
        raise Exception("生成私钥不符合要求")
    secret_key = str(bin(secret_key))[2:]
    g = point
    for i in range(1, len(secret_key)):
        g = E_double(g)
        if secret_key[i] == '1':
            g = E_add(g, point)
    return g

# 以下函数为求压缩公钥相关
def base58(address_hex):
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    b58_string = ''
    leading_zeros = len(address_hex) - len(address_hex.lstrip('0'))
    address_int = int(address_hex, 16)
    while address_int > 0:
        digit = address_int % 58
        digit_char = alphabet[digit]
        b58_string = digit_char + b58_string
        address_int //= 58
    ones = leading_zeros // 2
    for one in range(ones):
        b58_string = '1' + b58_string
    return b58_string


def sha_256(a):
    a = json.dumps(a).encode()
    a = hashlib.sha256(a).hexdigest()
    return a


def rip1(a):
    a = json.dumps(a).encode()
    a = hashlib.new('ripemd160', a).hexdigest()
    return a
# 以上函数为求压缩公钥相关

# https://en.bitcoin.it/wiki/Technical_background_of_version_1_Bitcoin_addresses
def get_address(sk):
    pubk = Emultiply(G_point, sk)
    # sa 是压缩公钥
    if pubk[1] % 2 == 1:
        sa = '03' + hex(pubk[0])[2:]
    else:
        sa = '02' + hex(pubk[0])[2:]
    tmpa = sha_256(sa)
    tmpa = rip1(tmpa)
    tmpa_body = '00' + tmpa
    tmpa = tmpa_body
    tmpa = sha_256(tmpa)
    prefix = sha_256(tmpa)[:8]
    pro_address = tmpa_body + prefix
    return pubk, base58(pro_address)


def sign(h, privkey):
    msg = int(hashlib.sha256(json.dumps(h).encode()).hexdigest(), 16)
    RandNum = random.randint(1, _r)
    xRand, yRand = Emultiply(G_point, RandNum)
    r = xRand % _r
    s = ((msg + r * privkey) * (Mod_inv(RandNum, _r))) % _r
    return [r, s]


def verify_sign(h, pubkey, rs):
    msg = int(hashlib.sha256(json.dumps(h).encode()).hexdigest(), 16)
    w = Mod_inv(rs[1], _r)
    xu1, yu1 = Emultiply(G_point, (msg * w) % _r)
    xu2, yu2 = Emultiply(pubkey, (rs[0] * w) % _r)
    x, y = E_add((xu1, yu1), (xu2, yu2))
    return x == rs[0]


if __name__ == '__main__':
    sk = 0x18e14a7b6a307f426a94f8114701e7c8e774e7f9a47e2c2035db29a206321725
    pubk = Emultiply(G_point, sk)
    # sa 是压缩公钥
    if pubk[1] % 2 == 1:
        sa = '03' + hex(pubk[0])[2:]
    else:
        sa = '02' + hex(pubk[0])[2:]
    print(hex(sk))
    print(pubk)
    print(hex(pubk[0]))
    print(sa)
    signature = sign(h, sk)
    print(signature)
    print(verify_sign(h, pubk, signature))
    # 随便修改一下签名
    signature[0] = signature[0] + 1
    print(verify_sign(h, pubk, signature))
    input('请输入任意字符退出')

