import re

p145 = '''
Bucket 0: [Node(144)]
Bucket 1: [Node(146), Node(147)]
Bucket 2: [Node(148), Node(149), Node(150)]
Bucket 4: [Node(129), Node(128), Node(131), Node(130), Node(133), Node(132), Node(135), Node(134), Node(137), Node(136), Node(139), Node(138), Node(141), Node(140), Node(143), Node(142)]
Bucket 7: [Node(17), Node(16), Node(19)]
'''


p146 = '''
Bucket 0: [Node(147)]
Bucket 1: [Node(145), Node(144)]
Bucket 2: [Node(148), Node(149), Node(150)]
Bucket 4: [Node(130), Node(131), Node(128), Node(129), Node(134), Node(135), Node(132), Node(133), Node(138), Node(139), Node(136), Node(137), Node(142), Node(143), Node(140), Node(141)]
Bucket 7: [Node(18), Node(19)]
'''

p145_nodes = re.findall(r'Node\((\d+)\)', p145)
p145_nodes = list(map(int, p145_nodes))

p146_nodes = re.findall(r'Node\((\d+)\)', p146)
p146_nodes = list(map(int, p146_nodes))

print(max([(p^145, p) for p in p145_nodes], key=lambda y: y[0]))
print(max([(p^146, p) for p in p146_nodes], key=lambda y: y[0]))
