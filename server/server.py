# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID
# Student: Mebrahtom & Erwan
# ------------------------------------------------------------------------------------------------------
import traceback
import sys
import time
import json
import argparse
from threading import Thread
from bottle import Bottle, run, request, template
import requests
# ------------------------------------------------------------------------------------------------------
try:
    app = Bottle()
    board = {0:"nothing",} 
    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def add_new_element_to_store(entry_sequence, element, is_propagated_call=False):
    	"""Adds an element to the board

    	Args:
    		entry_sequence(int): Identified the newly added element.
    		element(str/int/float): The actual element to be displayed on the board.
    		is_propagated_call(bool,optional): Indicates whether or not a call 
    			to this method is a propagated call. Defaults to False.

		Returns:
			bool:True if successful, False otherwise.

    	"""
        global board, node_id
        success = False
        try:
            board[int(entry_sequence)] = element
            success = True
        except Exception as e:
            print e
        return success

    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call = False):
    	"""Modifies an element in the board

    	Args:
    		entry_sequence(int): Serves as an id to identify each element.
    		modified_element(str/int/float): The new updated element on the board.
    		is_propagated_call(bool,optional): Indicates whether or not a call 
    			to this method is a propagated call. Defaults to False.

		Returns:
			bool:True if successful, False otherwise.
			
    	"""
        global board, node_id
        success = False
        try:
            board[int(entry_sequence)] = modified_element
            success = True
        except Exception as e:
            print e
        return success

    def delete_element_from_store(entry_sequence, is_propagated_call = False):
    	"""Deletes an element from the board

    	Args:
    		entry_sequence(int): Identifies the element to be deleted.
    		is_propagated_call(bool,optional): Indicates whether or not a call 
    			to this method is a propagated call. Defaults to False.

		Returns:
			bool:True if successful, False otherwise.
			
    	"""
        global board, node_id
        success = False
        try:
            del board[int(entry_sequence)]
            success = True
        except Exception as e:
            print e
        return success

    # ------------------------------------------------------------------------------------------------------
    # DISTRIBUTED COMMUNICATIONS FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def contact_vessel(vessel_ip, path, payload=None, req='POST'):
        """Conacts another server(vessel) through a POST or GET request, once.

    	Args:
    		vessel_ip(str): The IP address of a server, can be represented as a strig.
    		path(str): The url to which the POST request is sent.
    		payload(int/str): The data (element) sent to the path on a POST request.
    		req(string, optional): The type of request. Its value is either POST or GET. Defaults to POST.  

		Returns:
			bool:True if successful, False otherwise.
			
    	"""
        success = False
        try:
            if 'POST' in req:
                res = requests.post('http://{}{}'.format(vessel_ip, path), data=payload)
            elif 'GET' in req:
                res = requests.get('http://{}{}'.format(vessel_ip, path))
            else:
                print 'Non implemented feature!'
            # result is in res.text or res.json()
            print(res.text)
            if res.status_code == 200:
                success = True
        except Exception as e:
            print e
        return success

    def propagate_to_vessels(path, payload = None, req = 'POST'):
    	"""Propagates a message(element) to other vessels (servers).

    	Args:
    		path(str): The url to which the POST request is propagated.
    		payload(str/int/float): The data (element) propagated to the path on a POST request.
    		req(string, optional): The type of request. Its value is either POST or GET. Defaults to POST.  

		Note:
			Prints an error message if not successfull, nothing otherwise.
			
    	"""
        global vessel_list, node_id
        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id: # don't propagate to yourself
                success = contact_vessel(vessel_ip, path, payload, req)
                if not success:
                    print "\n\nCould not contact vessel {}\n\n".format(vessel_id)
    # ------------------------------------------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------------------------------------------
    @app.route('/')
    def index():
        global board, node_id
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()), members_name_string='YOUR NAME')

    @app.get('/board')
    def get_board():
        global board, node_id
        print board
        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()))
    
    @app.post('/board')
    def client_add_received():
        """Adds a new element to the board, propagates the add action to the other vessels.
        Called directly when a user is doing a POST request on /board. 

		Returns:
			bool:True if successful, False otherwise.
			
    	"""
        global board, node_id
        try:
            new_entry = request.forms.get('entry')
            max_sequence = max(board,key=int)
            new_sequence = max_sequence+1
            add_new_element_to_store(new_sequence, new_entry) 
            thread=Thread(target=propagate_to_vessels,args=('/propagate/add/{}'.format(new_sequence),new_entry))
            thread.deamon= True
            thread.run()
            return True
        except Exception as e:
            print e
        return False

    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
    	"""Deletes an element from or modifies an element at the board, 
    		propagates the delete/modify action to the other vessels.
    	Called directly when a user is doing a POST request on /board/element_id. 

        Args:
			element_id(int): The id of the element to be deleted/modified.

		Returns:
			bool:True if successful, False otherwise.

		"""
        try:
            delete=request.forms.get('delete')
            if delete=='0':
                current_element=request.forms.get('entry')
                modify_element_in_store(element_id,current_element)
                thread = Thread(target=propagate_to_vessels,args=('/propagate/modify/{}'.format(element_id),current_element))
                thread.deamon= True
                thread.run()
                return True
            elif delete=='1':
                delete_element_from_store(element_id)
                thread = Thread(target=propagate_to_vessels,args=('/propagate/delete/{}'.format(element_id),""))
                thread.deamon= True 
                thread.run()
                return True
        except Exception as e:
            print e
        return False

    @app.post('/propagate/<action>/<element_id>')
    def propagation_received(action, element_id):
        """Checks the type of action propagated and calls the corresponding functions.
        Called when propagation is received from another vessel(server).

        Args:
        	action(str): The type of action to be performed. 
        		The possible values are add, mofify, and delete. 
    		element_id(int): The id of an element to be added, modified of deleted.

		Returns:
			bool:True if successful, False otherwise.

		"""
        try:
            if action == 'add':
                add_new_element_to_store(element_id,request.body.read(),True)
                return True
            elif action == 'modify':
                modify_element_in_store(element_id,request.body.read(),True)
                return True
            elif action == 'delete':
                delete_element_from_store(element_id,True)
                return True
        except Exception as e:
            print e
        return False
        
    # ------------------------------------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------------------------------------
    # Execute the code
    def main():
        global vessel_list, node_id, app
        port = 80
        parser = argparse.ArgumentParser(description='Your own implementation of the distributed blackboard')
        parser.add_argument('--id', nargs='?', dest='nid', default=1, type=int, help='This server ID')
        parser.add_argument('--vessels', nargs='?', dest='nbv', default=1, type=int, help='The total number of vessels present in the system')
        args = parser.parse_args()
        node_id = args.nid
        vessel_list = dict()
        # We need to write the other vessels IP, based on the knowledge of their number
        for i in range(1, args.nbv+1):
            vessel_list[str(i)] = '10.1.0.{}'.format(str(i))

        try:
            run(app, host=vessel_list[str(node_id)], port=port)
        except Exception as e:
            print e
    # ------------------------------------------------------------------------------------------------------
    if __name__ == '__main__':
        main()
except Exception as e:
        traceback.print_exc()
        while True:
            time.sleep(60.)