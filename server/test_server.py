
from server import add_new_element_to_store
from server import delete_element_from_store
from server import modify_element_in_store

import unittest
class TestServer(unittest.TestCase):
	def test_add_new_element_to_store(self):	
		status=add_new_element_to_store(2,"hi")
		self.assertTrue(status)
	def test_delete_element_from_server(self):
		status=delete_element_from_store(2)
		self.assertTrue(status)
	def test_modify_element_from_store(self):
		status=modify_element_in_store(2,"Hello")
		self.assertTrue(status)
if __name__ == '__main__':
	unittest.main()
