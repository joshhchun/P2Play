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
	return parser.parse_args()

def run_test(*args):
	print(f"Running test with args: {args}")
	p = subprocess.Popen(['./JoinNetwork.py', *args], stdout=subprocess.PIPE)
 
def main():
	args = parse_arguments()
	num  = args.num
	ip   = args.ip
	path = pathlib.Path(__file__).parent.absolute() / "kad_files"

	_id           = 1
	bs_ip         = args.ip
	ports_to_use  = [9177 + i for i in range(num)]
	ports_used    = []
	threads       = []

	# First node in network
	port = 		ports_to_use[0]
	print(f"Using ({ip}:{port}) for node {_id}")
	t = threading.Thread(target=run_test, args=[str(_id), str(ip), str(port), path])
	threads.append(t)
	t.start()

	for i in range(1, num):
		_id   += 1
		port    = ports_to_use[i]
		bs_port = ports_to_use[i-1]
		print(f"Using ({ip}:{port}) for node {_id} with bs_port {bs_port}")
		t = threading.Thread(target=run_test, args=[str(_id), str(ip), str(port), path, str(bs_ip), str(bs_port)])
		threads.append(t)
		t.start()
		time.sleep(0.3)
	
	for t in threads:
		t.join()
	
		
if __name__ == '__main__':
	main()

