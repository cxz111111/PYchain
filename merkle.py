import hashlib


def merkle_tree(hash_t_list):
    if len(hash_t_list) == 1:
        return hash_t_list[0]
    new_list = []
    # len(hash_t_list)-1为列表末尾数的下标
    for i in range(0, len(hash_t_list)-1, 2):
        new_list.append(merkle_hash(hash_t_list[i], hash_t_list[i+1]))
    if len(hash_t_list) % 2 == 1:
        new_list.append(merkle_hash(hash_t_list[-1], hash_t_list[-1]))
    return merkle_tree(new_list)

def merkle_hash(a,b):
    c = (a+b).encode()
    c = hashlib.sha256((hashlib.sha256(c).hexdigest()).encode()).hexdigest()
    return c

if __name__ == '__main__':
    a = ['a', 'b', 'c', 'd', 'f', 'e']
    b = ['a', 'b', 'c', 'd', 'f', 'a']
    print((merkle_tree(a)))
    print((merkle_tree(b)))


