from deposit.gui import (DModel)

from lib.fnc_strat import *
from lib.fnc_export import *

from lib.History import (History)

from natsort import natsorted

STRAT_RELATIONS = ["included_by", "same_as", "cut_by", "covered_by", "abutted_by", "overlaps"]

STRAT_RELATIONS_DICT = {
	"Cut by": "cut_by",
	"Covered by": "covered_by",
	"Abutted by": "abutted_by",
	"Included by": "included_by",
	"Same as": "same_as",
	"Overlaps": "overlaps",
}

class Model(DModel):
	
	def __init__(self):
		
		self.features = {}  # {obj_id: label, ...}
		self.areas = {}  # {label: [obj_id, ...], ...}
		self.relations = []  # [[obj_id1, obj_id2, label], ...]
		self.obj_id_lookup = {}  # {node_id: [obj_id, ...], ...}
		self.graph_all = None
		self._descriptors = None  # (feature_cls, feature_descr, area_cls, area_descr)
		self._area = None
		self._strat_settings = None # (circular_only, join_contemporary, sort_by_phasing)
		
		DModel.__init__(self)
		
		self.history = History()
	
	def has_history(self):
		
		return self.history.can_undo()
	
	def has_data(self):
		
		return (len(self.features) > 0)
	
	def clear(self):
		
		DModel.clear(self)
		
		self.clear_data()
	
	def clear_data(self):
		
		self.features.clear()
		self.areas.clear()
		self.relations.clear()
		self.obj_id_lookup.clear()
		self.graph_all = None
	
	def set_area(self, area):
		
		self._area = area
	
	def set_strat_settings(self, circular_only, join_contemporary, sort_by_phasing):
		
		self._strat_settings = (circular_only, join_contemporary, sort_by_phasing)
	
	def set_descriptors(self, feature_cls, feature_descr, area_cls, area_descr):
		
		self._descriptors = (feature_cls, feature_descr, area_cls, area_descr)
	
	def load_data(self):
		
		self.clear_data()
		
		if self._descriptors is None:
			return
		feature_cls, feature_descr, area_cls, area_descr = self._descriptors
		for cls in [feature_cls, feature_descr, area_cls, area_descr]:
			if (cls is None) or (cls not in self.classes):
				return
		
		self.graph_all = nx.Graph()
		
		for feature_id in self.classes[feature_cls].objects:
			self.features[feature_id] = str(self.objects[feature_id].descriptors[feature_descr].label.value)
		for area_id in self.classes[area_cls].objects:
			area_label = str(self.objects[area_id].descriptors[area_descr].label.value)
			self.areas[area_label] = []
			for feature_id in self.objects[area_id].relations["contains"]:
				if feature_id not in self.features:
					continue
				self.areas[area_label].append(feature_id)
		self.areas = dict([(area_label, self.areas[area_label]) for area_label in natsorted(list(self.areas.keys()))])
		for feature_id1 in self.features:
			for rel in self.objects[feature_id1].relations:
				if rel in STRAT_RELATIONS:
					for feature_id2 in self.objects[feature_id1].relations[rel]:
						self.relations.append([feature_id1, feature_id2, rel])
						self.graph_all.add_edge(feature_id1, feature_id2)
	
	def get_areas(self):
		# returns areas = {label: [obj_id, ...], ...}
		
		if not self.has_data():
			self.load_data()
		return self.areas
	
	def get_graph(self):
		# returns nodes, edges, positions
		#
		# nodes = {node_id: label, ...}
		# edges = [[source_id, target_id, label, color], ...]
		# positions = {node_id: (x, y), ...}
		
		empty = ({}, [], {})
		
		if self._strat_settings is None:
			return empty
		
		if self._area not in self.areas:
			return empty
		
		circular_only, join_contemporary, sort_by_phasing = self._strat_settings
		
		if not self.has_data():
			self.load_data()
		features = dict([(obj_id, self.features[obj_id]) for obj_id in self.features if obj_id in self.areas[self._area]])
		relations = [[source_id, target_id, label] for source_id, target_id, label in self.relations if (source_id in self.areas[self._area]) and (target_id in self.areas[self._area])]
		
		nodes, edges, positions, self.obj_id_lookup = get_graph_elements(features, relations, circular_only, join_contemporary, sort_by_phasing)
		
		return nodes, edges, positions
	
	def get_node_objects(self, node_id):
		
		if node_id in self.obj_id_lookup:
			obj_ids = set(self.obj_id_lookup[node_id])
			obj_ids.update(find_all_connected(self.graph_all, obj_ids))
			return sorted(list(obj_ids))
		return []
	
	def get_feature_id(self, obj_id):
		
		if obj_id not in self.features:
			return ""
		return self.features[obj_id]
	
	def get_objects_for_relation(self, nodes):
		
		if len(nodes) != 2:
			return []
		objs_1 = self.get_node_objects(nodes[0])
		objs_2 = self.get_node_objects(nodes[1])
		if (len(objs_1) != 1) or (len(objs_2) != 1):
			return []
		
		return [objs_1[0], objs_2[0]]
	
	def add_relation(self, obj_ids, rel):
		
		if len(obj_ids) != 2:
			return
		obj_id1, obj_id2 = obj_ids
		self.objects[obj_id1].add_relation(rel, obj_id2)
		self.history.add(("add_relation", [[obj_id1], [obj_id2], rel]))
		self.load_data()
	
	def remove_relations(self, edges):
		
		data = []
		for node_id1, node_id2, label in edges:
			rel = STRAT_RELATIONS_DICT[label]
			obj_ids1 = self.get_node_objects(node_id1)
			obj_ids2 = self.get_node_objects(node_id2)
			for obj_id1 in obj_ids1:
				if rel not in self.objects[obj_id1].relations:
					continue
				for obj_id2 in obj_ids2:
					if obj_id2 not in self.objects[obj_id1].relations[rel]:
						continue
					self.objects[obj_id1].del_relation(rel, obj_id2)
					data.append([obj_id1, obj_id2, rel])
		self.history.add(("remove_relations", data))
		self.load_data()
	
	def reverse_relation_direction(self, edge):
		
		node_id1, node_id2, label = edge
		rel = STRAT_RELATIONS_DICT[label]
		if rel not in ["cut_by", "covered_by", "abutted_by"]:
			return
		obj_ids1 = self.get_node_objects(node_id1)
		obj_ids2 = self.get_node_objects(node_id2)
		data = []
		for obj_id1 in obj_ids1:
			if rel not in self.objects[obj_id1].relations:
				continue
			for obj_id2 in obj_ids2:
				if obj_id2 not in self.objects[obj_id1].relations[rel]:
					continue
				del self.objects[obj_id1].relations[rel][obj_id2]
				self.objects[obj_id2].add_relation(rel, obj_id1)
				data.append([obj_id1, obj_id2, rel])
		self.history.add(("reverse_relations", data))
		self.load_data()
	
	def undo(self):
		
		if not self.history.can_undo():
			return
		action, data = self.history.undo()
		if action == "add_relation":
			obj_ids1, obj_ids2, rel = data
			for obj_id1 in obj_ids1:
				for obj_id2 in obj_ids2:
					self.objects[obj_id1].del_relation(rel, obj_id2)
			
		elif action == "remove_relations":
			for obj_id1, obj_id2, rel in data:
				self.objects[obj_id1].add_relation(rel, obj_id2)
		
		elif action == "reverse_relations":
			for obj_id1, obj_id2, rel in data:
				del self.objects[obj_id2].relations[rel][obj_id1]
				self.objects[obj_id1].add_relation(rel, obj_id2)
		
		else:
			return
		self.load_data()
	
	def export_changes(self, path):
		
		actions = self.history.get_actions()
		if actions:
			relations_dict = dict([(STRAT_RELATIONS_DICT[key], key) for key in STRAT_RELATIONS_DICT])
			export_changes(actions, self.features, path, relations_dict)
	
	def export_xls(self, path):
		
		nodes, edges, _ = self.get_graph()
		if not nodes:
			return
		# nodes = {node_id: label, ...}
		# edges = [[source_id, target_id, label, color], ...]
		export_stratigraphy(nodes, edges, path)
	
	def data_source_changed_event(self):
		
		self.history.clear()
		DModel.data_source_changed_event(self)

