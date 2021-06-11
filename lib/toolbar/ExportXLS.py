from lib.toolbar._Tool import (Tool)

class ExportXLS(Tool):
	
	def name(self):
		
		return "Export Stratigraphy As XLS"
	
	def icon(self):
		
		return "export_xls.svg"
	
	def help(self):
		
		return "Export Stratigraphy As XLS"
	
	def enabled(self):
		
		return self.model.has_data()
	
	def triggered(self, state):
		
		self.view.export_xls()

