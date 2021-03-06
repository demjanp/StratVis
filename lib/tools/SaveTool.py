from deposit.gui import (Tool)

class SaveTool(Tool):

	def name(self):

		return "Save"

	def icon(self):

		return "save.svg"

	def help(self):

		if self.model.data_source is None:
			return "Save"
		
		save_to = self.model.data_source.__class__.__name__
		
		if hasattr(self.model.data_source, "url") and self.model.data_source.url:
			save_to = self.model.data_source.url
		elif hasattr(self.model.data_source, "connstr") and self.model.data_source.connstr:
			save_to = self.model.data_source.connstr
		
		return "Save to %s" % (save_to)

	def enabled(self):

		return self.model.is_connected()

	def triggered(self, state):
		
		self.view.save()

