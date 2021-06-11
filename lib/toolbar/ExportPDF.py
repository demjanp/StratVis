from lib.toolbar._Tool import (Tool)

class ExportPDF(Tool):
	
	def name(self):
		
		return "Export Stratigraphy As PDF"
	
	def icon(self):
		
		return "export_pdf.svg"
	
	def help(self):
		
		return "Export Stratigraphy As PDF"
	
	def enabled(self):
		
		return self.model.has_data()
	
	def triggered(self, state):
		
		self.view.export_pdf()

