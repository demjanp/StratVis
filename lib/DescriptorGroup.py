
from deposit.gui import (Button, LineEdit, Combo, SubView)

from PySide2 import (QtWidgets, QtCore, QtGui)

class DescriptorGroup(SubView, QtWidgets.QGroupBox):
	
	load_data = QtCore.Signal()
	
	def __init__(self, model, view):
		
		SubView.__init__(self, model, view)
		QtWidgets.QGroupBox.__init__(self, "Class / Descriptors")
		
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.feature_edit = LineEdit("Feature.Id")
		self.area_edit = LineEdit("Area.Id")
		
		classes_frame = QtWidgets.QFrame()
		classes_frame.setLayout(QtWidgets.QFormLayout())
		classes_frame.layout().setContentsMargins(0, 0, 0, 0)
		
		classes_frame.layout().addRow(QtWidgets.QLabel("Feature:"), self.feature_edit)
		classes_frame.layout().addRow(QtWidgets.QLabel("Area:"), self.area_edit)
		
		self.load_data_button = Button("Reload Graph", self.on_load_data)
		
		self.layout().addWidget(classes_frame)
		self.layout().addWidget(self.load_data_button)
		
		self.update()
		
		self.model.signal_data_source_changed.connect(self.on_data_changed)
		self.model.signal_data_changed.connect(self.on_data_changed)
	
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
	
	@QtCore.Slot()
	def on_data_changed(self):
		
		self.update()
	
	@QtCore.Slot()
	def on_load_data(self):
		
		self.load_data.emit()
