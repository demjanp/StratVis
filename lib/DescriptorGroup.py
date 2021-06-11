
from lib.Button import (Button)
from lib.LineEdit import (LineEdit)

from deposit.DModule import (DModule)
from deposit import Broadcasts

from PySide2 import (QtWidgets, QtCore, QtGui)

class DescriptorGroup(DModule, QtWidgets.QGroupBox):
	
	load_data = QtCore.Signal()
	
	def __init__(self, view):
		
		self.view = view
		self.model = view.model
		
		DModule.__init__(self)
		QtWidgets.QGroupBox.__init__(self, "Class / Descriptors")
		
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.feature_edit = LineEdit("Feature.Id")
		self.area_edit = LineEdit("Area.Id")
		
		classes_frame = QtWidgets.QFrame()
		classes_frame.setLayout(QtWidgets.QFormLayout())
		classes_frame.layout().setContentsMargins(0, 0, 0, 0)
		
		classes_frame.layout().addRow(QtWidgets.QLabel("Feature:"), self.feature_edit)
		classes_frame.layout().addRow(QtWidgets.QLabel("Area:"), self.area_edit)
		
		self.load_data_button = Button("Load Data", self.on_load_data)
		
		self.layout().addWidget(classes_frame)
		self.layout().addWidget(self.load_data_button)
		
		self.update()
		
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED, self.on_store_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_CHANGED, self.on_store_changed)
	
	def update(self):
		
		self.load_data_button.setEnabled(self.model.is_connected())
	
	def get_descriptors(self):
		
		values = self.feature_edit.get_value().split(".")
		if len(values) != 2:
			return None, None, None, None
		feature_cls, feature_descr = [val.strip() for val in values]
		values = self.area_edit.get_value().split(".")
		if len(values) != 2:
			return None, None, None, None
		area_cls, area_descr = [val.strip() for val in values]
		if "" in [feature_cls, feature_descr, area_cls, area_descr]:
			return None, None, None, None
		
		return feature_cls, feature_descr, area_cls, area_descr
	
	def on_store_changed(self, *args):
		
		self.update()
	
	@QtCore.Slot()
	def on_load_data(self):
		
		self.load_data.emit()
