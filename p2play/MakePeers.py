#!/usr/bin/env python3
import subprocess
import threading
import sys
import random
import time
import argparse
import pathlib

def parse_arguments():
	parser = argparse.ArgumentParser()

	parser.add_argument("-ip", "--ip", help="IP of these nodes", type=str, default=None)
	parser.add_argument("-n",  "--num", help="Number of nodes", type=int, default=70)
	parser.add_argument("-p",  "--port", help="port", type=int, default=9000)
	return parser.parse_args()

def run_test(*args):
	print(f"Running test with args: {args}")
	p = subprocess.Popen(['./JoinNetwork.py', *args], stdout=subprocess.PIPE)
 
def main():
	args = parse_arguments()
	num  = args.num
	ip   = args.ip
	path = pathlib.Path(__file__).absolute() / 

	_id           = 1
	bs_ip         = "student10.cse.nd.edu"
	ports_to_use  = [args.port + i for i in range(num)]
	ports_used    = []
	threads       = []

	# First node in network
	port = 		ports_to_use[0]
	print(f"Using ({ip}:{port}) for node {_id}")
	t = threading.Thread(target=run_test, args=[str(_id), str(ip), str(port)])
	threads.append(t)
	t.start()

	for i in range(1, num-1):
		_id   += 1
		port    = ports_to_use[i]
		bs_port = ports_to_use[i-1]
		print(f"Using ({ip}:{port}) for node {_id} with bs_port {bs_port}")
		t = threading.Thread(target=run_test, args=[str(_id), str(ip), str(port), str(bs_ip), str(bs_port)])
		threads.append(t)
		t.start()
		time.sleep(0.3)
	
	for t in threads:
		t.join()
	
		
if __name__ == '__main__':
	main()

