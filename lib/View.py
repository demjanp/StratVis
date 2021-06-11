
from lib.fnc_export import *

from lib.Model import (Model)
from lib.dialogs._Dialogs import (Dialogs)
from lib.toolbar._Toolbar import (Toolbar)
from lib.menu._Menu import Menu
from lib.StatusBar import (StatusBar)
from lib.Progress import (Progress)
from lib.DescriptorGroup import (DescriptorGroup)
from lib.AreaGroup import (AreaGroup)
from lib.StratigraphyGroup import (StratigraphyGroup)

from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.Registry import (Registry)
from deposit.commander.frames.GraphVisView import (GraphVisView)

from PySide2 import (QtWidgets, QtCore, QtGui)
from pathlib import Path
import deposit
import res
import os

class View(DModule, QtWidgets.QMainWindow):
	
	def __init__(self):
		
		self.model = None
		
		DModule.__init__(self)
		QtWidgets.QMainWindow.__init__(self)
		
		self.model = Model(self)
		
		self.registry = Registry("Deposit")
		self.dialogs = Dialogs(self)
		self.toolbar = Toolbar(self)
		self.menu = Menu(self)
		self.statusbar = StatusBar(self)
		self.progress = Progress(self)
		self.graph_view = GraphVisView()
		self.descriptor_group = DescriptorGroup(self)
		self.area_group = AreaGroup(self)
		self.stratigraphy_group = StratigraphyGroup(self)
		
		self.setWindowIcon(self.get_icon("sv_icon.svg"))
		self.setStyleSheet("QPushButton {padding: 5px; min-width: 100px;}")
		
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
		control_frame.layout().addStretch()
		
		graph_view_frame.layout().addWidget(self.graph_view)
		
		self.setStatusBar(self.statusbar)
		
		self.menu.load_recent()
		
		self.set_title()
#		self.setGeometry(100, 100, 1024, 768)
		self.setGeometry(500, 100, 1024, 768)  # DEBUG
		
		self.descriptor_group.load_data.connect(self.on_load_data)
		self.area_group.area_changed.connect(self.on_area_changed)
		self.stratigraphy_group.add_relation.connect(self.on_add_relation)
		self.stratigraphy_group.remove_relation.connect(self.on_remove_relation)
		self.stratigraphy_group.reverse_relation.connect(self.on_reverse_relation)
		self.stratigraphy_group.settings_changed.connect(self.on_strat_settings_changed)
		self.graph_view.selected.connect(self.on_graph_selected)
		self.graph_view.activated.connect(self.on_graph_activated)
		
		self.connect_broadcast(Broadcasts.VIEW_ACTION, self.on_view_action)
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_data_source_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED, self.on_data_source_changed)
		self.connect_broadcast(Broadcasts.STORE_DATA_CHANGED, self.on_data_changed)
		self.connect_broadcast(Broadcasts.STORE_SAVED, self.on_saved)
		self.connect_broadcast(Broadcasts.STORE_SAVE_FAILED, self.on_save_failed)
		self.set_on_broadcast(self.on_broadcast)
		
		self.model.broadcast_timer.setSingleShot(True)
		self.model.broadcast_timer.timeout.connect(self.on_broadcast_timer)
		
		self.update()
		
		self.dialogs.open("Connect")
	
	def set_title(self, name = None):

		title = "StratVis"
		if name is None:
			self.setWindowTitle(title)
		else:
			self.setWindowTitle("%s - %s" % (name, title))
	
	def update_mrud(self):
		
		if self.model.data_source is None:
			return
		if self.model.data_source.connstr is None:
			self.menu.add_recent_url(self.model.data_source.url)
		else:
			self.menu.add_recent_db(self.model.data_source.identifier, self.model.data_source.connstr)
	
	def update(self):
		
		if self.model.is_connected():
			self.set_title(os.path.split(str(self.model.identifier))[-1].strip("#"))
		area = self.get_area()
		areas = list(self.model.get_areas().keys())
		self.area_group.set_areas(areas, area)
		
		self.descriptor_group.update()
		self.area_group.update()
		self.stratigraphy_group.update()
	
	def save(self):
		
		if self.model.data_source is None:
			self.dialogs.open("Connect")
			
		else:
			self.progress.show("Saving...")
			self.model.save()
			self.progress.reset()
	
	def get_icon(self, name):

		path = os.path.join(os.path.dirname(res.__file__), name)
		if os.path.isfile(path):
			return QtGui.QIcon(path)
		path = os.path.join(os.path.dirname(deposit.__file__), "res", name)
		if os.path.isfile(path):
			return QtGui.QIcon(path)
		raise Exception("Could not load icon", name)
	
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
			self.dialogs.open("AddRelation", obj_ids)
	
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
	
	@QtCore.Slot()
	def on_graph_selected(self):
		
		self.update()
	
	@QtCore.Slot(int)
	def on_graph_activated(self, node_id):
		
		feature_cls, _, _, _ = self.get_descriptors()
		if feature_cls is None:
			return
		obj_ids = self.model.get_node_objects(node_id)
		self.model.launch_deposit()
		self.model.dc.view.query("SELECT %s.* WHERE id(%s) in {%s}" % (feature_cls, feature_cls, ",".join([str(obj_id) for obj_id in obj_ids])))
	
	def on_view_action(self, *args):
		
		pass
	
	def on_broadcast(self, signals):
		
		if (Broadcasts.STORE_SAVED in signals) or (Broadcasts.STORE_SAVE_FAILED in signals):
			self.process_broadcasts()
		else:
			self.model.broadcast_timer.start(100)
	
	def on_broadcast_timer(self):

		self.process_broadcasts()
	
	def on_data_source_changed(self, *args):
		
		self.set_title(os.path.split(str(self.model.identifier))[-1].strip("#"))
		self.statusbar.message("")
		self.update_mrud()
		self.update_graph()
		self.update()
	
	def on_data_changed(self, *args):
		
		self.statusbar.message("")
	
	def on_saved(self, *args):
		
		self.statusbar.message("Database saved.")
	
	def on_save_failed(self, *args):
		
		self.statusbar.message("Saving failed!")
	
	def closeEvent(self, event):
		
		if not self.model.is_saved():
			reply = QtWidgets.QMessageBox.question(self, "Exit", "Save changes to database?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
			if reply == QtWidgets.QMessageBox.Yes:
				self.save()
			elif reply == QtWidgets.QMessageBox.No:
				pass
			else:
				event.ignore()
				return
		
		self.model.on_close()
		QtWidgets.QMainWindow.closeEvent(self, event)
