from deposit.gui import (Tool)

class UndoTool(Tool):
	
	def name(self):
		
		return "Undo"
	
	def icon(self):
		
		return "undo.svg"
	
	def help(self):
		
		return "Undo last action"
	
	def enabled(self):
		
		return self.model.history.can_undo()
	
	def triggered(self, state):
		
		self.view.undo()

