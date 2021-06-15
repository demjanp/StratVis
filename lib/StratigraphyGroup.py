
from deposit.gui import (Button, CheckBox, SubView)

from PySide2 import (QtWidgets, QtCore, QtGui)

class StratigraphyGroup(SubView, QtWidgets.QGroupBox):
	
	add_relation = QtCore.Signal()
	remove_relation = QtCore.Signal()
	reverse_relation = QtCore.Signal()
	settings_changed = QtCore.Signal()
	
	def __init__(self, model, view):
		
		SubView.__init__(self, model, view)
		QtWidgets.QGroupBox.__init__(self, "Stratigraphy")
		
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.add_relation_button = Button("Add Relation", self.on_add_relation)
		self.remove_relation_button = Button("Remove Relation", self.on_remove_relation)
		self.reverse_relation_button = Button("Reverse Relation", self.on_reverse_relation)
		self.circular_only_checkbox = CheckBox("Show Circular Only", self.on_circular_only)
		self.join_contemporary_checkbox = CheckBox("Collapse Contemporary", self.on_join_contemporary)
		self.sort_by_phasing_checkbox = CheckBox("Sort By Phasing", self.on_sort_by_phasing)
		
		self.layout().addWidget(self.add_relation_button)
		self.layout().addWidget(self.remove_relation_button)
		self.layout().addWidget(self.reverse_relation_button)
		self.layout().addWidget(self.circular_only_checkbox)
		self.layout().addWidget(self.join_contemporary_checkbox)
		self.layout().addWidget(self.sort_by_phasing_checkbox)
		
		self.update()
		
		self.model.signal_data_source_changed.connect(self.on_data_changed)
		self.model.signal_data_changed.connect(self.on_data_changed)
	
	def update(self):
		
		nodes, edges = self.view.graph_view.get_selected()
		rel_objs = self.model.get_objects_for_relation(nodes)
		
		self.add_relation_button.setEnabled(len(rel_objs) == 2)
		self.remove_relation_button.setEnabled(len(edges) > 0)
		self.reverse_relation_button.setEnabled(len(edges) == 1)
		self.circular_only_checkbox.setEnabled(self.model.has_data())
		self.join_contemporary_checkbox.setEnabled(self.model.has_data())
		self.sort_by_phasing_checkbox.setEnabled(self.model.has_data())
	
	def get_settings(self):
		# returns circular_only, join_contemporary, sort_by_phasing
		
		return self.circular_only_checkbox.get_state(), self.join_contemporary_checkbox.get_state(), self.sort_by_phasing_checkbox.get_state()
	
	@QtCore.Slot()
	def on_add_relation(self):
		
		self.add_relation.emit()
	
	@QtCore.Slot()
	def on_remove_relation(self):
		
		self.remove_relation.emit()
	
	@QtCore.Slot()
	def on_reverse_relation(self):
		
		self.reverse_relation.emit()
	
	@QtCore.Slot()
	def on_circular_only(self):
		
		self.settings_changed.emit()
	
	@QtCore.Slot()
	def on_join_contemporary(self):
		
		self.settings_changed.emit()
	
	@QtCore.Slot()
	def on_sort_by_phasing(self):
		
		self.settings_changed.emit()
	
	@QtCore.Slot()
	def on_data_changed(self):
		
		self.update()

