
from deposit.store.Store import Store
from deposit.commander.Registry import Registry
import deposit
import res

from PySide2 import (QtWidgets, QtCore, QtGui)
from natsort import natsorted
from pathlib import Path
from os import system
import psycopg2
import sys
import os

class MainWindow(QtWidgets.QMainWindow):
	
	def __init__(self):
		
		QtWidgets.QMainWindow.__init__(self)
		
		self.registry = Registry("Gygaia2Deposit")
		
		self.setWindowTitle("Gygaia2Deposit")
		self.setWindowIcon(self.get_icon("g2d_icon.svg"))
		self.setStyleSheet("QPushButton {padding: 5px; min-width: 100px;}")
		
		central_widget = QtWidgets.QWidget(self)
		central_widget.setLayout(QtWidgets.QVBoxLayout())
		self.setCentralWidget(central_widget)
		
		self.setGeometry(100, 100, 800, 600)
		
		self.db_host_edit = QtWidgets.QLineEdit()
		self.db_host_edit.setText(self.get_from_registry("db_host"))
		self.db_port_edit = QtWidgets.QLineEdit()
		self.db_port_edit.setText(self.get_from_registry("db_port", "5432"))
		self.db_name_edit = QtWidgets.QLineEdit()
		self.db_name_edit.setText(self.get_from_registry("db_name"))
		self.db_user_edit = QtWidgets.QLineEdit()
		self.db_user_edit.setText(self.get_from_registry("db_user"))
		self.db_pass_edit = QtWidgets.QLineEdit()
		self.db_pass_edit.setEchoMode(QtWidgets.QLineEdit.Password)
		
		self.dep_path_edit = QtWidgets.QLineEdit()
		self.dep_path_edit.setText(self.get_from_registry("dep_path"))
		
		self.dep_path_button = QtWidgets.QToolButton()
		self.dep_path_button.setIcon(self.get_icon("open.svg"))
		self.dep_path_button.setIconSize(QtCore.QSize(24,24))
		self.dep_path_button.clicked.connect(self.on_dep_path)
		
		self.export_button = QtWidgets.QPushButton("Export")
		self.export_button.clicked.connect(self.on_export)
		self.export_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
		
		self.console_edit = QtWidgets.QTextEdit()
		self.console_edit.setReadOnly(True)
		self.console_edit.setFontPointSize(8)
		
		db_frame = QtWidgets.QGroupBox("Gygaia Database")
		db_frame.setLayout(QtWidgets.QFormLayout())
		db_frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		db_frame.layout().addRow("Host:", self.db_host_edit)
		db_frame.layout().addRow("Port:", self.db_port_edit)
		db_frame.layout().addRow("Database:", self.db_name_edit)
		db_frame.layout().addRow("Username:", self.db_user_edit)
		db_frame.layout().addRow("Password:", self.db_pass_edit)
		
		dep_frame = QtWidgets.QGroupBox("Deposit Database")
		dep_frame.setLayout(QtWidgets.QHBoxLayout())
		dep_frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		dep_frame.layout().addWidget(self.dep_path_edit)
		dep_frame.layout().addWidget(self.dep_path_button)
		
		export_frame = QtWidgets.QFrame()
		export_frame.setLayout(QtWidgets.QHBoxLayout())
		export_frame.layout().setContentsMargins(0, 0, 0, 0)
		export_frame.layout().addStretch()
		export_frame.layout().addWidget(self.export_button)
		export_frame.layout().addStretch()
		
		central_widget.layout().addWidget(db_frame)
		central_widget.layout().addWidget(dep_frame)
		central_widget.layout().addWidget(export_frame)
		central_widget.layout().addWidget(self.console_edit)
	
	def get_icon(self, name):

		path = os.path.join(os.path.dirname(res.__file__), name)
		if os.path.isfile(path):
			return QtGui.QIcon(path)
		path = os.path.join(os.path.dirname(deposit.__file__), "res", name)
		if os.path.isfile(path):
			return QtGui.QIcon(path)
		raise Exception("Could not load icon", name)
	
	def get_from_registry(self, key, default = ""):
		
		value = self.registry.get(key)
		if not value:
			value = default
		return value
	
	def write_console(self, text):
		
		text = str(text)
		if not text:
			return
		self.console_edit.append(text)
		QtWidgets.QApplication.processEvents()
	
	@QtCore.Slot()
	def on_dep_path(self):
		
		name = self.db_name_edit.text()
		if not name:
			name = "gygaia"
		default_path = self.registry.get("dep_path")
		if default_path:
			default_path = os.path.split(default_path)[0]
		if not default_path:
			default_path = os.path.join(str(Path.home()), "Desktop", name)
		path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Export As", default_path, "Deposit Pickle (*.pickle)")
		if path:
			self.dep_path_edit.setText(path)
	
	@QtCore.Slot()
	def on_export(self):
		
		db_host = self.db_host_edit.text().strip()
		db_port = self.db_port_edit.text().strip()
		db_name = self.db_name_edit.text().strip()
		db_user = self.db_user_edit.text().strip()
		db_pass = self.db_pass_edit.text().strip()
		dep_path = self.dep_path_edit.text().strip()
		if "" in [db_host, db_port, db_name, db_user, db_pass, dep_path]:
			self.write_console("Export Failed: Please fill in all fields")
			return
		
		try:
			conn = psycopg2.connect(dbname = db_name, user = db_user, password = db_pass, host = db_host, port = int(db_port))
			cursor = conn.cursor()
		except:
			self.write_console("Export Failed: Could not connect to Gygaia database")
			return
		
		try:
			cursor.execute("SELECT area_easting, area_northing, context_number, related_area_easting, related_area_northing, related_context_number, stratigraphic_relationship_type, stratigraphic_relationship_subtype FROM excavation.contexts_stratigraphic_relationships")
		except:
			_, exc_value, _ = sys.exc_info()
			self.write_console("Export Failed: Error querying Gygaia database")
			self.write_console(str(exc_value))
			return
		stratigraphy = []  # [[context1, relation, subtype, context2], ...]
		for row in cursor.fetchall():
			area_easting, area_northing, context_number, related_area_easting, related_area_northing, related_context_number, rel, subtype = row
			context1 = "%d.%d.%d" % (area_easting, area_northing, context_number)
			context2 = "%d.%d.%d" % (related_area_easting, related_area_northing, related_context_number)
			stratigraphy.append([context1, rel, subtype, context2])
		cursor.close()
		conn.close()
		
		self.registry.set("db_host", db_host)
		self.registry.set("db_port", str(db_port))
		self.registry.set("db_name", db_name)
		self.registry.set("db_user", db_user)
		self.registry.set("dep_path", dep_path)
		
		if os.path.isfile(dep_path):
			os.remove(dep_path)
		
		store = Store()
		store.load(os.path.abspath(dep_path))
		
		cls_feature = store.classes.add("Feature")
		cls_area = store.classes.add("Area")
		cls_sample = store.classes["Sample"]
		
		contexts = set([])
		for context1, rel, subtype, context2 in stratigraphy:
			contexts.add(context1)
			contexts.add(context2)
		for obj_id in cls_sample.objects:
			sample_id = store.objects[obj_id].descriptors["Id"].label.value
			context = ".".join(sample_id.split(".")[:3])
			contexts.add(context)
		
		contexts = natsorted(list(contexts))
		
		areas = set([])
		for context in contexts:
			area = ".".join(context.split(".")[:2])
			areas.add(area)
		areas = natsorted(list(areas))
		area_obj_lookup = {}
		for area in areas:
			area_obj_lookup[area] = cls_area.objects.add()
			area_obj_lookup[area].add_descriptor("Id", area)
		
		self.write_console("Connected to Gygaia database")
		self.write_console("Found %d stratigraphic relations between %d contexts in %d areas" % (len(stratigraphy), len(contexts), len(areas)))
		
		context_obj_lookup = {}
		for context in contexts:
			area = ".".join(context.split(".")[:2])
			context_obj_lookup[context] = cls_feature.objects.add()
			context_obj_lookup[context].add_descriptor("Id", context)
			area_obj_lookup[area].add_relation("contains", context_obj_lookup[context])
		
		for context1, rel, subtype, context2 in stratigraphy:
			
			rel_dep = None
			if (rel, subtype) == ("Contemporary with", "Included by"):
				rel_dep = "included_by"
			elif (rel, subtype) == ("Equal to", "Same as"):
				rel_dep = "same_as"
			elif (rel, subtype) == ("Earlier than", "Cut by"):
				rel_dep = "cut_by"
			elif (rel, subtype) == ("Earlier than", "Covered by"):
				rel_dep = "covered_by"
			elif (rel, subtype) == ("Earlier than", "Abutted by"):
				rel_dep = "abutted_by"
			elif (rel, subtype) == ("Non-contemporary", "Overlaps"):
				rel_dep = "overlaps"
			else:
				continue
			
			context_obj_lookup[context1].add_relation(rel_dep, context_obj_lookup[context2])
		
		for obj_id in cls_sample.objects:
			obj = store.objects[obj_id]
			sample_id = obj.descriptors["Id"].label.value
			context = ".".join(sample_id.split(".")[:3])
			context_obj_lookup[context].add_relation("contains", obj)
		
		store.save()
		self.write_console("Export to Deposit successfull. Created %d objects" % (len(store.objects)))

	
if __name__ == '__main__':
	
	system("title Gygaia2Deposit")
	
	app = QtWidgets.QApplication(sys.argv)
	main = MainWindow()
	main.show()
	app.exec_()
	
	