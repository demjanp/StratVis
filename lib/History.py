
from copy import copy

class History(object):
	
	def __init__(self):
		
		self._actions = []
	
	def clear(self):
		
		self._actions.clear()
	
	def can_undo(self):
		
		return (len(self._actions) > 0)
	
	def undo(self):
		
		if self._actions:
			return self._actions.pop()
	
	def add(self, action):
		
		self._actions.append(action)
	
	def get_actions(self):
		
		return copy(self._actions)

