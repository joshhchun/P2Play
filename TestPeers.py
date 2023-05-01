#!/usr/bin/env python3
import subprocess
import threading
import sys
import random
import time

def run_test(*args):
	print(f"Running test with args: {args}")
	p = subprocess.Popen(['./JoinNetwork.py', *args], stdout=subprocess.PIPE)
 
def main():
	num           = 70
	_id           = 1
	bs_ip         = "127.0.0.1"
	ports_to_use  = [9000 + i for i in range(num)]
	ports_used    = []
	threads       = []

	# First node in network
	# port    = ports_to_use.pop(random.randint(0, len(ports_to_use) - 1))
	port = 		ports_to_use[0]
	print(f"Using port {port} for node {_id}: {ports_to_use} left and {ports_used} used")
	# ports_used.append(port)
	t = threading.Thread(target=run_test, args=[str(_id), str(port)])
	threads.append(t)
	t.start()

	for i in range(1, num-1):
		_id   += 1
		# port    = ports_to_use.pop(random.randint(0, len(ports_to_use) - 1))
		port    = ports_to_use[i]
		# bs_port = random.choice(ports_used)
		bs_port = ports_to_use[i-1]
		# print(f"Using port {port} for node {_id}: {ports_to_use} left and {ports_used} used")
		print(f"Using port {port} for node {_id} with bs_port {bs_port}")
		t = threading.Thread(target=run_test, args=[str(_id), str(port), str(bs_ip), str(bs_port)])
		threads.append(t)
		t.start()
		time.sleep(0.3)
		# ports_used.append(port)
	
	for t in threads:
		t.join()
	
		
if __name__ == '__main__':
	main()

