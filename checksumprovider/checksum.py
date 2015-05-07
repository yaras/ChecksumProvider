#!/usr/bin/env python
"""
Script for calculating checksums. For the newest version visit https://github.com/yaras/ChecksumProvider.git
"""

import argparse
import hashlib
import os
import requests
from argparse import RawTextHelpFormatter
from timeit import default_timer as timer

__author__ = "yaras"
__copyright__ = "Copyright 2015"
__credits__ = ["yaras"]
__license__ = "MIT"
__version__ = "0.1.0"
__maintainer__ = "yaras"
__status__ = "Alpha"

class ChecksumFile:
	def __init__(self, path = None, checksum = None):
		self._path = path
		self._checksum = checksum

	@property
	def path(self):
		return self._path

	@path.setter
	def path(self, value):
		self._path = value

	@property
	def checksum(self):
	    return self._checksum

	@checksum.setter
	def checksum(self, value):
		self._checksum = value

class PathTraversalQueue:
	def __init__(self):
		self.files_queue = []
		self.directories_queue = []

	def push_file(self, path):
		self.files_queue.append(path)

	def push_directory(self, path):
		self.directories_queue.append(path)

	def get_paths(self):
		for p in self.files_queue:
			yield p

		for p in self.directories_queue:
			for (d, dirs, files) in os.walk(p):
				for f in files:
					yield os.path.join(d, f)

class ConsoleWriter:
	def write_file(self, file):
		if not isinstance(file, ChecksumFile):
			raise Exception('Expected ChecksumFile, but got {}'.format(file.__class__))

		print('{}\t{}'.format(file.path, file.checksum))

	def write_comment(self, comment):
		print(comment)

	def close(self):
		pass

class FileConsoleWriter(ConsoleWriter):
	def __init__(self, output):
		self.output = open(output, 'w')

	def write_file(self, file):
		ConsoleWriter.write_file(self, file)

		print('{}\t{}'.format(file.path, file.checksum), file=self.output)

	def close(self):
		ConsoleWriter.close(self)
		self.output.close()	

class VerificationFileReader:

	def __init__(self, path):
		self.path = path

	def read(self):
		with open(self.path) as input:
			for line in input:
				f = ChecksumFile(*line.strip().split('\t'))

				yield f

class VerificationResultConsoleWriter:
	def __init__(self):
		pass

	def write_success(self, file):
		print('OK\t{}'.format(file.path))

	def write_error(self, error):
		print('ERR\t{}'.format(file.path))

	def write_comment(self, comment):
		print(comment)

class Calculator:
	def calculate_checksums(self, writer, queue):
		if not isinstance(queue, PathTraversalQueue):
			raise Exception('Expected PathTraversalQueue, but got {}'.format(queue.__class__))

		if not isinstance(writer, ConsoleWriter):
			raise Exception('Expected ConsoleWriter, but got {}'.format(writer.__class__))

		count = 0
		t = timer()

		try:
			for path in queue.get_paths():
				f = ChecksumFile(path, self.__hash(path))
				writer.write_file(f)

				count += 1
		finally:
			writer.write_comment('--------------')
			writer.write_comment('Calculated hashes:\t{}'.format(count))
			writer.write_comment('Time:\t\t\t\t{} s'.format(timer() - t))

		writer.close()

	def verify_checksums(self, reader, result_writer):
		if not isinstance(reader, VerificationFileReader):
			raise Exception('Expected VerificationFileReader, but got {}'.format(reader.__class__))

		if not isinstance(result_writer, VerificationResultConsoleWriter):
			raise Exception('Expected VerificationResultConsoleWriter, but got {}'.format(result_writer.__class__))

		count = 0
		t = timer()

		all_valid = True

		for file in reader.read():
			actual = self.__hash(file.path)

			if actual == file.checksum:
				result_writer.write_success(file)
			else:
				result_writer.write_error(file)
				all_valid = False

			count += 1

		result_writer.write_comment('--------------')
		result_writer.write_comment('All valid:\t\t\t{}'.format(all_valid))
		result_writer.write_comment('Calculated hashes:\t{}'.format(count))
		result_writer.write_comment('Time:\t\t\t\t{} s'.format(timer() - t))

	def __hash(self, file, blocksize=2**20):
		m = hashlib.sha1()

		with open(file, 'rb') as f:
			while True:
				buf = f.read(blocksize)
				if not buf:
					break
				m.update( buf )
    
		return m.hexdigest()		

def main(args):
	c = Calculator()

	if args.verify:
		reader = VerificationFileReader(args.verify)
		result_writer = VerificationResultConsoleWriter()

		c.verify_checksums(reader, result_writer)
	else:
		queue = PathTraversalQueue()

		if args.file:
			queue.push_file(args.file)

		if args.directory:
			queue.push_directory(args.directory)		

		if args.output:
			writer = FileConsoleWriter(args.output)
		else:
			writer = ConsoleWriter()		
		
		c.calculate_checksums(writer, queue)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, description='''Calculates checksums for files or directories.

Examples:

	Calculate checksum for file 'checksum.py' and print it on console
		checksum.py --file checksum.py

	Calculate checksum for file 'checksum.py', print it on console and save to 'checksum.py.sha1'
		checksum.py --file checksum.py --output checksum.py.sha1

	Calculate checksums for each file in directory 'test' and save to 'test.sha1'
		checksum.py --directory test --output test.sha1
''')

	parser.add_argument('-f', '--file', help='File to calculate checksum')
	parser.add_argument('-d', '--directory', help='Directory to calculate checksums')
	parser.add_argument('-o', '--output', help='Output file to save result')
	parser.add_argument('-v', '--verify', help='Verify checksums from file')
	args = parser.parse_args()

	if not args.file and not args.directory and not args.verify: # and not args.network:
		print(parser.print_help())
	else:
		main(args)