
from PySide2 import (QtWidgets, QtCore, QtGui)
from openpyxl.styles import (Font)
from openpyxl import Workbook
from natsort import natsorted
from pathlib import Path
import csv
import os

def get_save_path(name, registry):
	
	default_path = registry.get("export_dir")
	if not default_path:
		default_path = os.path.join(str(Path.home()), "Desktop", name)
	path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Export As", default_path, "Excel 2007+ Workbook (*.xlsx);;Comma-separated Values (*.csv)")
	
	return path

def write_spreadsheet(columns, rows, path):
	
	if path.lower().endswith(".csv"):
		with open(path, "w", newline = "") as f:
			writer = csv.writer(f, dialect=csv.excel, quoting=csv.QUOTE_ALL)
			writer.writerow(columns)
			for row in rows:
				writer.writerow(row)
	
	elif path.lower().endswith(".xlsx"):
		wb = Workbook()
		wb.guess_types = False
		ws = wb.active
		ws.append(columns)
		for i in range(len(columns)):
			ws.cell(row = 1, column = i + 1).font = Font(bold = True)
		for row in rows:
			ws.append(row)
		wb.save(path)

def export_changes(actions, features, path, relations_dict):
	# actions = [[action, data], ...]
	# features = {obj_id: label, ...}
	# relations_dict = {rel: label, ...}
	
	columns = ["Action", "Source", "Relation", "Target"]
	rows = []
	for action, data in actions:
		if action == "add_relation":
			obj_id1, obj_id2, rel = data
			obj_id1 = obj_id1[0]
			obj_id2 = obj_id2[0]
			rows.append(["add_relation", features[obj_id1], relations_dict[rel], features[obj_id2]])
		
		elif action == "remove_relations":
			for obj_id1, obj_id2, rel in data:
				rows.append(["remove_relation", features[obj_id1], relations_dict[rel], features[obj_id2]])
		
		elif action == "reverse_relations":
			for obj_id1, obj_id2, rel in data:
				rows.append(["reverse_relation", features[obj_id1], relations_dict[rel], features[obj_id2]])
	write_spreadsheet(columns, rows, path)

def export_stratigraphy(nodes, edges, path):
	# nodes = {node_id: label, ...}
	# edges = [[source_id, target_id, label, color], ...]
	
	columns = ["Source", "Relation", "Target", "Circular"]
	rows = []
	nodes_done = set([])
	for source_id, target_id, label, color in edges:
		nodes_done.add(source_id)
		nodes_done.add(target_id)
		rows.append([nodes[source_id], label, nodes[target_id], 1 if color == "red" else ""])
	rows = natsorted(rows, key = lambda row: row[0])
	write_spreadsheet(columns, rows, path)
	
	