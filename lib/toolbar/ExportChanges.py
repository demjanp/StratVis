from lib.toolbar._Tool import (Tool)

class ExportChanges(Tool):
	
	def name(self):
		
		return "Export Changes"
	
	def icon(self):
		
		return "export_changes.svg"
	
	def help(self):
		
		return "Export Changes as XLS"
	
	def enabled(self):
		
		return self.model.history.can_undo()
	
	def triggered(self, state):
		
		self.view.export_changes()

