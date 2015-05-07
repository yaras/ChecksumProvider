import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from checksumprovider.checksum import Calculator
from checksumprovider.checksum import PathTraversalQueue
from checksumprovider.checksum import ChecksumFile
from checksumprovider.checksum import VerificationFileReader
from checksumprovider.checksum import VerificationResultConsoleWriter
from checksumprovider.checksum import ConsoleWriter

class BufferedWriter(ConsoleWriter):
	def __init__(self):
		self.files = []
		self.comments = []

	def write_file(self, file):
		if not isinstance(file, ChecksumFile):
			raise Exception('Expected ChecksumFile, but got {}'.format(file.__class__))

		self.files.append('{}\t{}'.format(file.path, file.checksum))

	def write_comment(self, comment):
		self.comments.append(comment)

class BufferedVerificationResultWriter(VerificationResultConsoleWriter):

	def __init__(self):
		self.successes = []
		self.errors = []

	def write_success(self, file):
		self.successes.append(file)

	def write_error(self, file):
		self.errors.append(file)

class VerificationListReader(VerificationFileReader):

	def __init__(self, l):
		self.list = l

	def read(self):
		for i in self.list:
			yield i

class CalculatorTests(unittest.TestCase):
	def test_calculate_checksums(self):
		queue = PathTraversalQueue()
		queue.push_directory('resources')

		writer = BufferedWriter()

		c = Calculator()

		c.calculate_checksums(writer, queue)

		for f in writer.files:
			print(f)

		self.assertEqual(4, len(writer.files))

		self.assertEqual('resources\\new file.txt\t6e7df2009255d3e0d83ace22a7f0c16443dc7144', writer.files[0])
		self.assertEqual('resources\\text\t136b630ac4670a8ab29f5e018562d0addce6b8cc', writer.files[1])
		self.assertEqual('resources\\a\\j.json\t01538b01b5bcd793be876d487056c210f04b6097', writer.files[2])
		self.assertEqual('resources\\a\\new.xml\td2260eaa90e8f8640f1c0fc2204a67d67614a006', writer.files[3])

	def test_verify_checksums(self):
		result_writer = BufferedVerificationResultWriter()

		reader = VerificationListReader([  
			ChecksumFile('resources\\new file.txt', '6e7df2009255d3e0d83ace22a7f0c16443dc7144'),
			ChecksumFile('resources\\text', '136b630ac4670a8ab29f5e018562d0addce6b8cc'),
			ChecksumFile('resources\\a\\j.json', '01538b01b5bcd793be876d487056c210f04b6097')
		])

		c = Calculator()

		c.verify_checksums(reader, result_writer)

		self.assertEqual(3, len(result_writer.successes))
		self.assertEqual(1, len([l for l in result_writer.successes if l.path == 'resources\\new file.txt']))
		self.assertEqual(1, len([l for l in result_writer.successes if l.path == 'resources\\text']))
		self.assertEqual(1, len([l for l in result_writer.successes if l.path == 'resources\\a\\j.json']))

		self.assertEqual(0, len(result_writer.errors))

	def test_verify_checksums_error(self):
		result_writer = BufferedVerificationResultWriter()

		reader = VerificationListReader([  
			ChecksumFile('resources\\new file.txt', '6e7df2009255d3e0d83ace22a7f0c16443dc7144'),
			ChecksumFile('resources\\text', '136b630ac467baaaaaaaad18562d0addce6b8cc'),
			ChecksumFile('resources\\a\\j.json', '01538b01b5bcd793be876d487056c210f04b6097')
		])

		c = Calculator()

		c.verify_checksums(reader, result_writer)

		self.assertEqual(2, len(result_writer.successes))
		self.assertEqual(1, len([l for l in result_writer.successes if l.path == 'resources\\new file.txt']))
		self.assertEqual(1, len([l for l in result_writer.successes if l.path == 'resources\\a\\j.json']))

		self.assertEqual(1, len(result_writer.errors))
		self.assertEqual(1, len([l for l in result_writer.errors if l.path == 'resources\\text']))

	def test_calculate_invalid_queue(self):
		c = Calculator()

		writer = BufferedVerificationResultWriter()
		
		try:
			c.calculate_checksums(writer, {})
			self.fail('expected exception')
		except Exception as ex:
			self.assertEqual('Expected PathTraversalQueue, but got <class \'dict\'>', str(ex))

	def test_calculate_invalid_writer(self):
		c = Calculator()

		queue = PathTraversalQueue()

		try:
			c.calculate_checksums({}, queue)
			self.fail('expected exception')
		except Exception as ex:
			self.assertEqual('Expected ConsoleWriter, but got <class \'dict\'>', str(ex))

	def test_verify_invalid_consolewriter(self):
		c = Calculator()

		reader = VerificationFileReader('')

		try:
			c.verify_checksums(reader, {})
			self.fail('expected exception')
		except Exception as ex:
			self.assertEqual('Expected VerificationResultConsoleWriter, but got <class \'dict\'>', str(ex))

class PathTraversalQueueTests(unittest.TestCase):
	def test_push_file(self):
		q = PathTraversalQueue()

		q.push_file('__init__.py')

		all_files = list(q.get_paths())

		self.assertEqual(1, len(all_files))
		self.assertEqual('__init__.py', all_files[0])

	def test_push_files(self):
		q = PathTraversalQueue()

		q.push_file('a')
		q.push_file('b')
		q.push_file('c')

		all_files = list(q.get_paths())

		self.assertEqual(3, len(all_files))
		self.assertEqual('a', all_files[0])
		self.assertEqual('b', all_files[1])
		self.assertEqual('c', all_files[2])

	def test_push_directory(self):
		q = PathTraversalQueue()

		q.push_directory('resources')

		all_files = list(q.get_paths())

		self.assertEqual(4, len(all_files))
		self.assertEqual('resources\\new file.txt', all_files[0])
		self.assertEqual('resources\\text', all_files[1])
		self.assertEqual('resources\\a\\j.json', all_files[2])
		self.assertEqual('resources\\a\\new.xml', all_files[3])

	def test_push_files_directories(self):
		q = PathTraversalQueue()

		q.push_file('a')
		q.push_file('b')
		q.push_directory('resources')	

		all_files = list(q.get_paths())

		self.assertEqual(6, len(all_files))

		self.assertEqual('a', all_files[0])
		self.assertEqual('b', all_files[1])
		self.assertEqual('resources\\new file.txt', all_files[2])
		self.assertEqual('resources\\text', all_files[3])
		self.assertEqual('resources\\a\\j.json', all_files[4])
		self.assertEqual('resources\\a\\new.xml', all_files[5])

class ChecksumFileTests(unittest.TestCase):
	def test_init(self):
		f = ChecksumFile('aa', 'bb')

		self.assertEqual('aa', f.path)
		self.assertEqual('bb', f.checksum)

	def test_set_path(self):
		f = ChecksumFile()
		f.path = 'aa'

		self.assertEqual('aa', f.path)

	def test_set_checksum(self):
		f = ChecksumFile()
		f.checksum = 'aa'

		self.assertEqual('aa', f.checksum)

class ConsoleWriterTests(unittest.TestCase):
	def test_no_checksumfile(self):
		writer = ConsoleWriter()

		try:
			writer.write_file({})
		except Exception as e:
			self.assertEqual('Expected ChecksumFile, but got <class \'dict\'>', str(e))

	def test_write_file(self):
		writer = ConsoleWriter()
		writer.write_file(ChecksumFile('aa', 'bb'))		

class VerificationFileReaderTests(unittest.TestCase):
	def test_read(self):
		reader = VerificationFileReader('dummy_checksums.txt')

		result = list(reader.read())

		self.assertEqual(2, len(result))

		self.assertEqual(1, len([l for l in result if l.path == 'resources\\text']))
		self.assertEqual(1, len([l for l in result if l.path == 'resources\\newfile.txt']))

if __name__ == '__main__':
    unittest.main()