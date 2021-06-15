
from deposit.gui import (LineEdit, SubView)

from PySide2 import (QtWidgets, QtCore, QtGui)

class SearchGroup(SubView, QtWidgets.QGroupBox):
	
	search_signal = QtCore.Signal(str)
	
	def __init__(self, model, view):
		
		SubView.__init__(self, model, view)
		QtWidgets.QGroupBox.__init__(self, "Find Feature")
		
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.search_edit = LineEdit(callback = self.on_search)
		
		self.layout().addWidget(self.search_edit)
	
	@QtCore.Slot(str)
	def on_search(self, text):
		
		self.search_signal.emit(text)
