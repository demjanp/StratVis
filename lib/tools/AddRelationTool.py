from deposit.gui import (Tool)

class AddRelationTool(Tool):
	
	def name(self):
		
		return "Add Relation"
	
	def icon(self):
		
		return "link.svg"
	
	def help(self):
		
		return "Add Relation"
	
	def enabled(self):
		
		nodes, edges = self.view.graph_view.get_selected()
		rel_objs = self.model.get_objects_for_relation(nodes)
		
		return (len(rel_objs) == 2)
	
	def triggered(self, state):
		
		self.view.on_add_relation()
	