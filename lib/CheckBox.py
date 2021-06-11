
from PySide2 import (QtWidgets, QtCore, QtGui)

class CheckBox(QtWidgets.QCheckBox):
	
	def __init__(self, caption, callback):
		
		QtWidgets.QCheckBox.__init__(self, caption)
		
		self.stateChanged.connect(callback)
	
	def set_state(self, state):
		
		self.blockSignals(True)
		self.setChecked(state)
		self.blockSignals(False)
	
	def get_state(self):
		
		return self.isChecked()
	
