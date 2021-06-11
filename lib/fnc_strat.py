import numpy as np
import networkx as nx
import multiprocessing as mp
from natsort import natsorted
from itertools import combinations
from collections import defaultdict
from networkx.drawing.nx_agraph import graphviz_layout

def get_contexts(stratigraphy, p_included_by = 1, p_same_as = 0.5, p_cut_by = 1, p_covered_by = 0.8, p_abutted_by = 0.3, p_overlaps = 1):
	# returns contexts, contemporary, chronostrat_contexts
	# contexts = [context, ...]
	# contemporary[ci1, ci2] = p; ci = index in contexts; p = probability that ci1 and ci2 are contemporary
	# chronostrat_contexts[ci1, ci2] = p; ci = index in contexts; p = probability that ci1 is earlier than ci2
	
	rel_lookup = {
		"included_by": p_included_by,
		"same_as": p_same_as,
		"cut_by": p_cut_by,
		"covered_by": p_covered_by,
		"abutted_by": p_abutted_by,
		"overlaps": p_overlaps,
	}
	
	contexts = set([])
	for context1, context2, rel in stratigraphy:
		contexts.add(context1)
		contexts.add(context2)
	contexts = natsorted(list(contexts))
	contemporary = np.zeros((len(contexts), len(contexts)), dtype = np.float64)
	chronostrat_contexts = np.zeros((len(contexts), len(contexts)), dtype = np.float64)
	for context1, context2, rel in stratigraphy:
		ci1 = contexts.index(context1)
		ci2 = contexts.index(context2)
		if rel in ["cut_by", "covered_by", "abutted_by"]:
			chronostrat_contexts[ci1, ci2] = rel_lookup[rel]
		elif rel in ["included_by", "same_as"]:
			contemporary[ci1, ci2] = rel_lookup[rel]
			contemporary[ci2, ci1] = rel_lookup[rel]
		elif rel == "overlaps":
			chronostrat_contexts[ci1, ci2] = p_overlaps
			chronostrat_contexts[ci2, ci1] = p_overlaps
	
	contemporary[np.diag_indices(len(contexts))] = 1
	
	return np.array(contexts), contemporary, chronostrat_contexts

def find_groups(relation_matrix):
	
	G = nx.from_numpy_matrix(relation_matrix, create_using = nx.Graph)
	groups = []
	for c in nx.connected_components(G):
		G_sub = G.subgraph(c)
		groups.append(np.array(list(G_sub.nodes), dtype = int))
	return groups

def remove_circulars(contemporary, chronostrat):
	
	def has_circulars(G, check_edges):
		
		for i, j in check_edges:
			if nx.has_path(G, j, i):
				return True
		return False
	
	def find_updated_circulars(G, i, j, check_edges):
		
		G.remove_edge(i, j)
		G.remove_edge(j, i)
		collect = set([])
		for k, l in check_edges:
			if nx.has_path(G, l, k):
				collect.add((k, l))
		G.add_edge(i, j)
		G.add_edge(j, i)
		return collect
	
	# collapse relations
	contemporary_collapsed = (np.random.random(contemporary.shape) < contemporary)
	contemporary_collapsed = np.triu(contemporary_collapsed) | np.triu(contemporary_collapsed).T
	chronostrat_collapsed = (np.random.random(chronostrat.shape) < chronostrat)
	
	removed_contemporary = np.zeros(contemporary.shape, dtype = bool)
	
	# remove circulars caused by entered earlier-than relations
	for i, j in np.argwhere(chronostrat_collapsed & np.triu(chronostrat_collapsed).T):
		# chronostrat_collapsed[i,j] & chronostrat_collapsed[j,i] = True
		# pick which relation to keep
		remove = []
		if chronostrat[i, j] > chronostrat[j, i]:
			remove = [j, i]
		elif chronostrat[i, j] < chronostrat[j, i]:
			remove = [i, j]
		else:
			remove = [[i, j], [j, i]][np.random.randint(2)]
		i, j = remove
		chronostrat_collapsed[i, j] = False
	
	for group in find_groups(chronostrat_collapsed):
		if len(group) < 2:
			continue
		G = nx.from_numpy_matrix(chronostrat_collapsed[np.ix_(group, group)], create_using = nx.DiGraph)
		circulars = set([])
		ps = []
		for i, j in G.edges:
			if (j, i) in circulars:
				continue
			if nx.has_path(G, j, i):
				circulars.add((i, j))
				ps.append(chronostrat[group[i], group[j]])
		if circulars:
			check_edges = circulars
			ps = np.array(ps, dtype = np.float64)
			circulars = np.array(list(circulars), dtype = int)
			idxs = np.hstack([np.random.permutation(np.where(ps == p)[0]) for p in np.sort(np.unique(ps))])
			for idx in idxs:
				i, j = circulars[idx]
				if nx.has_path(G, j, i):
					G.remove_edge(i, j)
					check_edges.remove((i, j))
					chronostrat_collapsed[group[i], group[j]] = False
				if not has_circulars(G, check_edges):
					break
	
	# remove conflicts between earlier-than and contemporary relations
	mask = (contemporary_collapsed & (chronostrat_collapsed | chronostrat_collapsed.T))
	contemporary_collapsed[mask] = False
	removed_contemporary[mask] = True
	
	# remove circulars caused by contemporary relations
	contemporary_collapsed[np.diag_indices(contemporary_collapsed.shape[0])] = False
	last_found = True
	found = True
	while True:
		G = nx.from_numpy_matrix(chronostrat_collapsed | contemporary_collapsed, create_using = nx.DiGraph)
		circular_cis = set([])
		check_edges = set([])
		for i, j in G.edges:
			if contemporary_collapsed[i, j]:
				continue
			if nx.has_path(G, j, i):
				check_edges.add((i, j))
				if contemporary_collapsed[i].any():
					circular_cis.add(i)
				if contemporary_collapsed[j].any():
					circular_cis.add(j)
		if not circular_cis:
			break
		G_units = nx.from_numpy_matrix(contemporary_collapsed, create_using = nx.Graph)
		circulars = set([])
		ps = []
		for i, j in G_units.edges:
			if circular_cis.intersection([i, j]):
				circulars.add((i, j))
				ps.append(contemporary[i, j])
		if not circulars:
			break
		last_found = found
		found = False
		if circulars:
			ps = np.array(ps, dtype = np.float64)
			circulars = np.array(list(circulars), dtype = int)
			idxs = np.hstack([np.random.permutation(np.where(ps == p)[0]) for p in np.sort(np.unique(ps))])
			done = set([])
			for idx in idxs:
				i, j = circulars[idx]
				if (i, j) in done:
					continue
				if not last_found:
					found = True
					contemporary_collapsed[i, j] = False
					contemporary_collapsed[j, i] = False
					G.remove_edge(i, j)
					G.remove_edge(j, i)
					done.add((j, i))
					removed_contemporary[i, j] = True
					removed_contemporary[j, i] = True
					if not has_circulars(G, check_edges):
						break
				else:
					new_edges = find_updated_circulars(G, i, j, check_edges)
					if len(new_edges) < len(check_edges):
						found = True
						check_edges = new_edges
						contemporary_collapsed[i, j] = False
						contemporary_collapsed[j, i] = False
						G.remove_edge(i, j)
						G.remove_edge(j, i)
						done.add((j, i))
						removed_contemporary[i, j] = True
						removed_contemporary[j, i] = True
	
	# attempt to add back some of the removed contemporary relations (higher probability first)
	if removed_contemporary.any():
		ijs = np.argwhere(np.triu(removed_contemporary))
		ps = contemporary[np.triu(removed_contemporary)].flatten()
		idxs = np.hstack([np.random.permutation(np.where(ps == p)[0]) for p in np.sort(np.unique(ps))])[::-1]
		check_edges = set([(i, j) for i, j in np.argwhere(chronostrat_collapsed)])
		for idx in idxs:
			i, j = ijs[idx]
			G.add_edge(i, j)
			G.add_edge(j, i)
			if not has_circulars(G, check_edges):
				contemporary_collapsed[i, j] = True
				contemporary_collapsed[j, i] = True
				removed_contemporary[i, j] = False
				removed_contemporary[j, i] = False
			else:
				G.remove_edge(i, j)
				G.remove_edge(j, i)
	
	contemporary_collapsed[np.diag_indices(contemporary_collapsed.shape[0])] = True
	
	return contemporary_collapsed, chronostrat_collapsed

def find_circulars(contemporary, chronostrat):
	# returns circulars[ci1, ci2] = True/False
	
	contemporary_collapsed = (contemporary > 0)
	contemporary_collapsed[np.diag_indices(contemporary_collapsed.shape[0])] = False
	contemporary_collapsed = np.triu(contemporary_collapsed) | np.triu(contemporary_collapsed).T
	chronostrat_collapsed = (chronostrat > 0)
	
	circulars = np.zeros(contemporary.shape, dtype = bool)
	for i, j in np.argwhere(chronostrat_collapsed & contemporary_collapsed):
		circulars[i, j] = True
		circulars[j, i] = True
	
	G = nx.from_numpy_matrix(chronostrat_collapsed | contemporary_collapsed, create_using = nx.DiGraph)
	for i, j in G.edges:
		if contemporary_collapsed[i, j]:
			continue
		if nx.has_path(G, j, i):
			circulars[i, j] = True
			circulars[j, i] = True
	
	G = nx.from_numpy_matrix(contemporary_collapsed, create_using = nx.Graph)
	units = find_groups(contemporary_collapsed)
	for unit in units:
		for i, j in np.argwhere(chronostrat_collapsed[np.ix_(unit, unit)]):
			circulars[unit[i], unit[j]] = True
			circulars[unit[j], unit[i]] = True
	
	return circulars

def get_phasing(G):
	# returns phasing = {node_id: [phase_min, phase_max], ...}
	
	def get_lower_phasing(chronostrat):
		
		n_nodes = chronostrat.shape[0]
		phasing = np.full(n_nodes, np.nan)  # phasing[idx] = phase; lower = earlier
		
		# assign phase to nodes latest to earliest
		mask_todo = chronostrat.copy()
		phase = 0
		while mask_todo.any():
			latest = (mask_todo.any(axis = 0) & ~mask_todo.any(axis = 1))
			phasing[latest] = phase
			mask_todo[:,latest] = False
			phase += 1
		
		# assign phases to nodes earliest to latest, if not already assigned
		mask_todo = chronostrat.copy()
		phase = n_nodes
		while mask_todo.any():
			earliest = (mask_todo.any(axis = 1) & ~mask_todo.any(axis = 0))
			phasing[np.isnan(phasing) & earliest] = phase
			mask_todo[earliest] = False
			phase -= 1
		
		# minimize range of phases
		vals = np.unique(phasing[~np.isnan(phasing)])
		vals.sort()
		collect = phasing.copy()
		for val_new, val in enumerate(vals):
			collect[phasing == val] = val_new
		phasing = collect
		
		mask = (~np.isnan(phasing))
		if mask.any():
			phasing[mask] = phasing[mask].max() - phasing[mask]
		
		return phasing
	
	def get_phasing_limits(idx, phasing_lower, idxs_later, idxs_earlier):
		
		phase_min = 0
		ph_later = phasing_lower[idxs_later[idx]]
		ph_later = ph_later[~np.isnan(ph_later)]
		if ph_later.size:
			phase_max = int(ph_later.min()) - 1
		else:
			phase_max = phasing_lower.max()
		ph_earlier = phasing_lower[idxs_earlier[idx]]
		ph_earlier = ph_earlier[~np.isnan(ph_earlier)]
		if ph_earlier.size:
			phase_min = int(ph_earlier.max()) + 1
		if np.isnan(phase_max):
			phase_max = phase_min
		return int(phase_min), int(phase_max)
	
	nodes = sorted(list(G.nodes()))
	n_nodes = len(nodes)
	chronostrat = np.zeros((n_nodes, n_nodes), dtype = bool)
	for gi, gj in G.edges():
		chronostrat[nodes.index(gi), nodes.index(gj)] = True
	
	idxs_later = [np.where(chronostrat[idx])[0] for idx in range(n_nodes)]
	idxs_earlier = [np.where(chronostrat[:,idx])[0] for idx in range(n_nodes)]
	
	phasing_lower = get_lower_phasing(chronostrat)
	
	phasing = {}  # {node_id: [phase_min, phase_max], ...}
	for idx in range(n_nodes):
		phase_min, phase_max = get_phasing_limits(idx, phasing_lower, idxs_later, idxs_earlier)
		phasing[nodes[idx]] = [phase_min, phase_max]
	
	return phasing

def get_graph_elements(features, relations, circular_only, join_contemporary, sort_by_phasing, p_included_by = 1, p_same_as = 0.5, p_cut_by = 1, p_covered_by = 0.8, p_abutted_by = 0.3, p_overlaps = 1, xscale = 1, yscale = 1):
	# features = {obj_id: label, ...}
	# relations = [[obj_id1, obj_id2, label], ...]
	# circular_only, join_contemporary, sort_by_phasing = True/False
	#
	# returns nodes, edges, positions, obj_id_lookup
	# nodes = {node_id: label, ...}
	# edges = [[source_id, target_id, label, color], ...]
	# positions = {node_id: (x, y), ...}
	# obj_id_lookup = {node_id: [obj_id, ...], ...}
	
	def update_vars(vars):
		
		for i in range(len(vars)):
			while True:
				found = False
				for j in range(len(vars)):
					if i == j:
						continue
					if vars[i] == vars[j]:
						vars[i] += 0.000000000001
						found = True
				if not found:
					break
		return vars
	
	if (not features) or (not relations):
		return {}, [], {}, {}
	
	# make sure all p_values are unique within contemporary and chronostrat relations (needed for looking up edge labels)
	p_included_by, p_same_as = update_vars([p_included_by, p_same_as])
	p_cut_by, p_covered_by, p_abutted_by, p_overlaps = update_vars([p_cut_by, p_covered_by, p_abutted_by, p_overlaps])
	
	names_contemporary = {
		p_included_by: "Included by",
		p_same_as: "Same as",
	}
	names_chronostrat = {
		p_cut_by: "Cut by",
		p_covered_by: "Covered by",
		p_abutted_by: "Abutted by",
		p_overlaps: "Overlaps",
	}
	
	contexts, contemporary, chronostrat = get_contexts(relations, p_included_by = p_included_by, p_same_as = p_same_as, p_cut_by = p_cut_by, p_covered_by = p_covered_by, p_abutted_by = p_abutted_by)
	circulars = find_circulars(contemporary, chronostrat)
	
	if circular_only:
		include = set(np.argwhere(circulars).flatten().tolist())
		for i in list(include):
			include.update(np.where(contemporary[i] > 0)[0].tolist())
		include = list(include)
		contexts = contexts[include]
		contemporary = contemporary[:,include][include]
		chronostrat = chronostrat[:,include][include]
		circulars = circulars[:,include][include]
	
	context_objs = {}
	if join_contemporary:
		while True:
			to_join = []
			idxs_joined = set([])
			units = find_groups((contemporary > 0))
			for unit in units:
				if len(unit) < 2:
					continue
				unit_slice = np.ix_(unit, unit)
				circulars_unit = circulars[unit_slice]
				exclude = set([])
				for i, j in np.argwhere(circulars_unit):
					if circulars_unit[j,i]:
						exclude.update({i, j})
				if exclude:
					unit = np.setdiff1d(unit, unit[list(exclude)])
				if len(unit) > 1:
					to_join.append(unit)
					idxs_joined.update(unit.tolist())
			if idxs_joined:
				contexts_lookup = {}
				context_objs = {}
				for i in range(len(contexts)):
					if i in idxs_joined:
						for unit in to_join:
							if i in unit:
								name = "%s.%s" % (".".join(features[contexts[i]].split(".")[:2]), ",".join(natsorted([features[contexts[j]].split(".")[-1] for j in unit])))
								contexts_lookup[i] = name
								context_objs[i] = [contexts[j] for j in unit]
								break
					else:
						contexts_lookup[i] = features[contexts[i]]
						context_objs[i] = [contexts[i]]
				contexts = natsorted(list(set(list(contexts_lookup.values()))))
				collect = {}
				for i in contexts_lookup:
					collect[contexts.index(contexts_lookup[i])] = context_objs[i]
				context_objs = collect
				contexts_n = len(contexts)
				collect = np.zeros((contexts_n, contexts_n), dtype = float)
				for i, j in np.argwhere(contemporary > 0):
					i_, j_ = contexts.index(contexts_lookup[i]), contexts.index(contexts_lookup[j])
					collect[i_, j_] = contemporary[i,j]
				contemporary = collect.copy()
				collect = np.zeros((contexts_n, contexts_n), dtype = float)
				for i, j in np.argwhere(chronostrat > 0):
					i_, j_ = contexts.index(contexts_lookup[i]), contexts.index(contexts_lookup[j])
					collect[i_, j_] = chronostrat[i,j]
				chronostrat = collect.copy()
				collect = np.zeros((contexts_n, contexts_n), dtype = bool)
				for i, j in np.argwhere(circulars):
					i_, j_ = contexts.index(contexts_lookup[i]), contexts.index(contexts_lookup[j])
					collect[i_, j_] = True
				circulars = collect.copy()
				contexts = np.array(contexts)
			else:
				break

	
	contemporary_collapsed, chronostrat_collapsed = remove_circulars((contemporary > 0).astype(float), (chronostrat > 0).astype(float))
	G = nx.from_numpy_matrix(chronostrat_collapsed, create_using = nx.DiGraph)
	
	positions = graphviz_layout(G, prog = "graphviz/dot.exe")
	
	if sort_by_phasing:
		phasing = get_phasing(G)  # {node_id: [phase_min, phase_max], ...}
		ymin, ymax = np.inf, -np.inf
		for i in positions:
			x, y = positions[i]
			ymin = min(ymin, y)
			ymax = max(ymax, y)
		phmax = 0
		diffmax = 0
		for i in phasing:
			phmax = max(phmax, phasing[i][1])
			diffmax = max(diffmax, phasing[i][1] - phasing[i][0])
		phstep = (ymax - ymin) / phmax
		done = set([])
		for i in positions:
			ph = (phasing[i][0] + phasing[i][1]) / 2
			diff = phasing[i][1] - phasing[i][0]
			x, y = positions[i][0], ymin + (phmax - ph) * phstep
			while (x, y) in done:
				y += phstep / 3
			done.add((x, y))
			positions[i] = (x * xscale, y * yscale)
	
	nodes = {}
	edges = []
	obj_id_lookup = {}
	for i, context in enumerate(contexts):
		if i in context_objs:
			nodes[i] = context
			obj_id_lookup[i] = context_objs[i]
		else:
			nodes[i] = features[context]
			obj_id_lookup[i] = [context]
	for i, j in np.argwhere(chronostrat > 0):
		color = "red" if circulars[i, j] else "black"
		edges.append([i, j, names_chronostrat[chronostrat[i,j]], color])
	for i, j in np.argwhere(np.triu(contemporary > 0)):
		if i == j:
			continue
		color = "red" if circulars[i, j] else "black"
		edges.append([i, j, names_contemporary[contemporary[i,j]], color])
		edges.append([j, i, names_contemporary[contemporary[i,j]], color])
	
	return nodes, edges, positions, obj_id_lookup
	
	