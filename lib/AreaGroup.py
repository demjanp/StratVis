
from deposit.gui import (Combo, SubView)

from PySide2 import (QtWidgets, QtCore, QtGui)

class AreaGroup(SubView, QtWidgets.QGroupBox):
	
	area_changed = QtCore.Signal()
	
	def __init__(self, model, view):
		
		SubView.__init__(self, model, view)
		QtWidgets.QGroupBox.__init__(self, "Area")
		
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.area_combo = Combo(self.on_area_changed)
		
		self.layout().addWidget(self.area_combo)
		
		self.update()
		
		self.model.signal_data_source_changed.connect(self.on_data_changed)
		self.model.signal_data_changed.connect(self.on_data_changed)
	
	def update(self):
		
		self.area_combo.setEnabled(self.model.has_data())
	
	def get_area(self):
		
		area = self.area_combo.get_value().strip()
		if not area:
			return None
		return area
	
	def set_areas(self, areas, default):
		
		self.area_combo.set_values(areas, default)
	
	@QtCore.Slot()
	def on_area_changed(self):
		
		self.update()
		self.area_changed.emit()
	
	@QtCore.Slot()
	def on_data_changed(self):
		
		self.update()
