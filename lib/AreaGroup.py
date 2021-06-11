
from lib.Combo import (Combo)

from deposit.DModule import (DModule)
from deposit import Broadcasts

from PySide2 import (QtWidgets, QtCore, QtGui)

class AreaGroup(DModule, QtWidgets.QGroupBox):
	
	area_changed = QtCore.Signal()
	
	def __init__(self, view):
		
		self.view = view
		self.model = view.model
		
		DModule.__init__(self)
		QtWidgets.QGroupBox.__init__(self, "Area")
		
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.area_combo = Combo(self.on_area_changed)
		
		self.layout().addWidget(self.area_combo)
		
		self.update()
		
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_data_source_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED, self.on_data_source_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_CHANGED, self.on_data_changed)
	
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
	
	def on_data_source_changed(self, *args):
		
		self.update()
	
	def on_data_changed(self, *args):
		
		self.update()
