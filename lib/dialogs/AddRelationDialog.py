
from deposit.gui import (Dialog, Button)

from PySide2 import (QtWidgets, QtCore, QtGui)

REL_VALUES = [
	["cut_by", "Cut by"],
	["covered_by", "Covered by"],
	["abutted_by", "Abutted by"],
	["included_by", "Included by"],
	["same_as", "Same as"],
	["overlaps", "Overlaps"],
]

class AddRelationDialog(Dialog):
	
	def title(self):
		
		return "Add Relation"
	
	def set_up(self, obj_ids):
		
		self.obj_ids = obj_ids
		
		self.setMinimumWidth(300)
		self.setModal(True)
		self.setLayout(QtWidgets.QVBoxLayout())
		
		font = QtGui.QFont("Calibri", 10, QtGui.QFont.Bold)
		
		self.feature_label1 = QtWidgets.QLabel()
		self.feature_label1.setFont(font)
		self.feature_label2 = QtWidgets.QLabel()
		self.feature_label2.setFont(font)
		self.relation_combo = QtWidgets.QComboBox()
		switch_button = Button("Switch", self.on_switch, self.view.get_icon("switch.svg"))
		switch_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
		self.relation_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		combo_frame = QtWidgets.QFrame()
		combo_frame.setLayout(QtWidgets.QHBoxLayout())
		combo_frame.layout().setContentsMargins(0, 0, 0, 0)
		combo_frame.layout().addWidget(switch_button)
		combo_frame.layout().addWidget(self.relation_combo)
		
		self.layout().addWidget(self.feature_label1)
		self.layout().addWidget(combo_frame)
		self.layout().addWidget(self.feature_label2)
		
		values = [row[1] for row in REL_VALUES]
		self.relation_combo.addItems(values)
		
		self.update_features()
	
	def update_features(self):
		
		self.feature_label1.setText("<strong>%s</strong>" % self.model.get_feature_id(self.obj_ids[0]))
		self.feature_label2.setText("<strong>%s</strong>" % self.model.get_feature_id(self.obj_ids[1]))
	
	def button_box(self):
		
		return True, True
	
	@QtCore.Slot()
	def on_switch(self):
		
		if self.obj_ids:
			self.obj_ids = self.obj_ids[::-1]
		self.update_features()
	
	def process(self):
		
		positions_saved = self.view.get_saved_positions()
		
		rel = REL_VALUES[self.relation_combo.currentIndex()][0]
		self.model.add_relation(self.obj_ids, rel)
		nodes, edges, positions = self.model.get_graph()
		attributes = dict([(node_id, [("", nodes[node_id])]) for node_id in nodes])
		self.view.graph_view.set_data(nodes, edges, attributes, positions, show_attributes = 1)
		
		self.view.set_saved_positions(positions_saved)
		
		self.view.update()
