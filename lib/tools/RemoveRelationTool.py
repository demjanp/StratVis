from deposit.gui import (Tool)

class RemoveRelationTool(Tool):
	
	def name(self):
		
		return "Remove Relation"
	
	def icon(self):
		
		return "unlink.svg"
	
	def help(self):
		
		return "Remove Relation"
	
	def enabled(self):
		
		_, edges = self.view.graph_view.get_selected()
		
		return (len(edges) > 0)
	
	def triggered(self, state):
		
		self.view.on_remove_relation()
	
	def shortcut(self):
		
		return "Del"
