
from lib.fnc_export import *

from deposit.gui import (DView, DMenu, DToolbar, Dialogs, GraphView, Separator)

from lib.dialogs.ConnectDialog import ConnectDialog
from lib.dialogs.AddRelationDialog import AddRelationDialog
from lib.dialogs.AboutDialog import AboutDialog

from deposit.gui import (ConnectTool, SaveTool, SaveAsFileTool, DepositTool, ClearRecentTool, AboutTool, LogFileTool)
from lib.tools.AddRelationTool import AddRelationTool
from lib.tools.RemoveRelationTool import RemoveRelationTool
from lib.tools.ExportChangesTool import ExportChangesTool
from lib.tools.ExportPDFTool import ExportPDFTool
from lib.tools.ExportXLSTool import ExportXLSTool
from lib.tools.SaveTool import SaveTool
from lib.tools.UndoTool import UndoTool

from lib.DescriptorGroup import DescriptorGroup
from lib.AreaGroup import AreaGroup
from lib.StratigraphyGroup import StratigraphyGroup
from lib.SearchGroup import SearchGroup

from PySide2 import (QtWidgets, QtCore, QtGui)

class View(DView):
	
	APP_NAME = "StratVis"
	
	def __init__(self, model):
		
		DView.__init__(self, model)
		
		self.graph_view = GraphView()
		self.dialogs = Dialogs(self, [ConnectDialog, AddRelationDialog, AboutDialog])
		self.toolbar = DToolbar(self, {
			"Data": [ConnectTool, SaveTool, DepositTool, Separator, AddRelationTool, RemoveRelationTool, Separator, UndoTool, Separator, ExportChangesTool, ExportXLSTool, ExportPDFTool],
		})
		self.menu = DMenu(self, {
			"Data": [ConnectTool, SaveTool, SaveAsFileTool, DepositTool, Separator, ClearRecentTool,],
			"Edit": [AddRelationTool, RemoveRelationTool, UndoTool,],
			"Export": [ExportChangesTool, ExportXLSTool, ExportPDFTool,],
			"Help": [AboutTool,],
		})
		self.descriptor_group = DescriptorGroup(self.model, self)
		self.area_group = AreaGroup(self.model, self)
		self.stratigraphy_group = StratigraphyGroup(self.model, self)
		self.search_group = SearchGroup(self.model, self)
		
		self.set_icon("sv_icon.svg")
		
		central_widget = QtWidgets.QWidget(self)
		central_widget.setLayout(QtWidgets.QHBoxLayout())
		central_widget.layout().setContentsMargins(0, 0, 0, 0)
		self.setCentralWidget(central_widget)
		
		control_frame = QtWidgets.QFrame(self)
		control_frame.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
		control_frame.setLayout(QtWidgets.QVBoxLayout())
		control_frame.layout().setContentsMargins(10, 10, 0, 10)
		
		graph_view_frame = QtWidgets.QFrame(self)
		graph_view_frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		graph_view_frame.setLayout(QtWidgets.QVBoxLayout())
		graph_view_frame.layout().setContentsMargins(0, 0, 0, 0)
		
		central_widget.layout().addWidget(control_frame)
		central_widget.layout().addWidget(graph_view_frame)
		
		control_frame.layout().addWidget(self.descriptor_group)
		control_frame.layout().addWidget(self.area_group)
		control_frame.layout().addWidget(self.stratigraphy_group)
		control_frame.layout().addWidget(self.search_group)
		control_frame.layout().addStretch()
		
		graph_view_frame.layout().addWidget(self.graph_view)
		
		self.descriptor_group.load_data.connect(self.on_load_data)
		self.area_group.area_changed.connect(self.on_area_changed)
		self.stratigraphy_group.add_relation.connect(self.on_add_relation)
		self.stratigraphy_group.remove_relation.connect(self.on_remove_relation)
		self.stratigraphy_group.reverse_relation.connect(self.on_reverse_relation)
		self.stratigraphy_group.settings_changed.connect(self.on_strat_settings_changed)
		self.search_group.search_signal.connect(self.on_search)
		self.graph_view.signal_selected.connect(self.on_graph_selected)
		self.graph_view.signal_activated.connect(self.on_graph_activated)
		
		self.model.signal_data_source_changed.connect(self.on_data_source_changed)
		
		self.update()
		
		self.dialogs.open("ConnectDialog")
	
	def update(self):
		
		self.model.set_area(self.get_area())
		self.model.set_strat_settings(*self.get_strat_settings())
		self.model.set_descriptors(*self.get_descriptors())
		
		area = self.get_area()
		areas = list(self.model.get_areas().keys())
		self.area_group.set_areas(areas, area)
		
		self.descriptor_group.update()
		self.area_group.update()
		self.stratigraphy_group.update()

	def get_descriptors(self):
		# returns feature_cls, feature_descr, area_cls, area_descr
		
		return self.descriptor_group.get_descriptors()
	
	def get_area(self):
		
		return self.area_group.get_area()
	
	def get_strat_settings(self):
		
		return self.stratigraphy_group.get_settings()
	
	def get_saved_positions(self):
		
		positions_saved = {}
		for node_id in self.graph_view._nodes:
			node = self.graph_view._nodes[node_id]
			pos = node.pos()
			x, y = pos.x(), pos.y()
			positions_saved[node.descriptors[0]] = (x, y)
		return positions_saved
	
	def set_saved_positions(self, positions):
		
		for node_id in self.graph_view._nodes:
			label = self.graph_view._nodes[node_id].descriptors[0]
			if label in positions:
				x, y = positions[label]
				self.graph_view._nodes[node_id].setPos(x, y)
		for edge in self.graph_view._edges:
			edge.adjust()
	
	def update_graph(self):
		
		nodes, edges, positions = self.model.get_graph()
		attributes = dict([(node_id, [("", nodes[node_id])]) for node_id in nodes])
		self.graph_view.set_data(nodes, edges, attributes, positions, show_attributes = 1)
	
	def undo(self):
		
		if not self.model.history.can_undo():
			return
		positions_saved = self.get_saved_positions()
		self.model.undo()
		nodes, edges, positions = self.model.get_graph()
		attributes = dict([(node_id, [("", nodes[node_id])]) for node_id in nodes])
		self.graph_view.set_data(nodes, edges, attributes, positions, show_attributes = 1)
		self.set_saved_positions(positions_saved)
		self.update()
	
	def export_changes(self):
		
		name = "%s_changes" % (self.model.identifier.split("/")[-1].strip("#"))
		path = get_save_path(name, self.registry)
		if not path:
			return
		self.model.export_changes(path)
		self.registry.set("export_dir", os.path.split(path)[0])
	
	def export_xls(self):
		
		area = self.get_area()
		name = "%s_%s" % (self.model.identifier.split("/")[-1].strip("#"), area.replace(".","_"))
		path = get_save_path(name, self.registry)
		if not path:
			return
		self.model.export_xls(path)
		self.registry.set("export_dir", os.path.split(path)[0])
	
	def export_pdf(self):
		
		area = self.get_area()
		name = "%s_%s.pdf" % (self.model.identifier.split("/")[-1].strip("#"), area.replace(".","_"))
		default_path = self.registry.get("export_dir")
		if not default_path:
			default_path = os.path.join(str(Path.home()), "Desktop", name)
		path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Export As", default_path, "Adobe PDF (*.pdf)")
		if not path:
			return
		self.graph_view.save_pdf(path)
		self.registry.set("export_dir", os.path.split(path)[0])
	
	@QtCore.Slot()
	def on_load_data(self):
		
		self.update()
		self.update_graph()
		self.update()
	
	@QtCore.Slot()
	def on_area_changed(self):
		
		self.update()
		self.update_graph()
	
	@QtCore.Slot()
	def on_add_relation(self):
		
		nodes, _ = self.graph_view.get_selected()
		obj_ids = self.model.get_objects_for_relation(nodes)
		if len(obj_ids) == 2:
			self.dialogs.open("AddRelationDialog", obj_ids)
	
	@QtCore.Slot()
	def on_remove_relation(self):
		
		_, edges = self.graph_view.get_selected()
		if len(edges) == 0:
			return
		reply = QtWidgets.QMessageBox.question(self, "Remove Relations?", "Remove the selected relations?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
		if reply != QtWidgets.QMessageBox.Yes:
			return
		positions_saved = self.get_saved_positions()
		self.model.remove_relations(edges)
		nodes, edges, positions = self.model.get_graph()
		attributes = dict([(node_id, [("", nodes[node_id])]) for node_id in nodes])
		self.graph_view.set_data(nodes, edges, attributes, positions, show_attributes = 1)
		self.set_saved_positions(positions_saved)
		self.update()
	
	@QtCore.Slot()
	def on_reverse_relation(self):
		
		_, edges = self.graph_view.get_selected()
		if len(edges) != 1:
			return
		positions_saved = self.get_saved_positions()
		self.model.reverse_relation_direction(edges[0])
		nodes, edges, positions = self.model.get_graph()
		attributes = dict([(node_id, [("", nodes[node_id])]) for node_id in nodes])
		self.graph_view.set_data(nodes, edges, attributes, positions, show_attributes = 1)
		self.set_saved_positions(positions_saved)
		self.update()
	
	@QtCore.Slot()
	def on_strat_settings_changed(self):
		
		self.update()
		self.update_graph()
	
	@QtCore.Slot(str)
	def on_search(self, text):
		
		node_ids = self.model.find_nodes(text)
		if node_ids:
			self.graph_view.deselect_all()
			for node_id in node_ids:
				self.graph_view.select_node(node_id)
	
	@QtCore.Slot()
	def on_graph_selected(self):
		
		self.update()
		self.changed_event()
	
	@QtCore.Slot(int)
	def on_graph_activated(self, node_id):
		
		feature_cls, _, _, _ = self.get_descriptors()
		if feature_cls is None:
			return
		obj_ids = self.model.get_node_objects(node_id)
		self.model.launch_deposit()
		self.model.deposit_gui.view.query("SELECT %s.* WHERE id(%s) in {%s}" % (feature_cls, feature_cls, ",".join([str(obj_id) for obj_id in obj_ids])))
	
	@QtCore.Slot(int)
	def on_data_source_changed(self):
		
		DView.on_data_source_changed(self)
		self.update_graph()
		self.update()
	
