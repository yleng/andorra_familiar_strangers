import cPickle
import csv
import os
import sys
import networkx as nx
import numpy as np
import json
import seaborn as sns
import update_encounters_json as up_encs
import getMaps as maps
from collections import defaultdict
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import itertools


def read_json_file_generator(json_filename,limit=float('inf')):
	with open(json_filename) as infile:
		for line in infile:
			yield json.loads(line)

def filter_xvals(json_filename,filter_func=lambda row:True):
	return [convert_row(row) for row in read_json_file_generator(json_filename) if filter_func(row)]

def graph_filter_vals(json_filename, filter_func):
	return [row['distance'] for row in read_json_file_generator(json_filename) if filter_func(row)]	

def create_graphs_on_tower_type(encounters_json, destination_path, n, bins=150, bin_range=[0,180], ignore_n=False):
	tower_map = maps.tower_to_activity()
	tower_types = get_tower_types(tower_map)
	axis_ranges = [50, 200, 500, 1000, 2000, 5000]
	for first, second in itertools.permutations(tower_types, 2):
		filter_func = create_loc_filter_func(first, second, n, tower_map,ignore_n=ignore_n)
		print 'retreiving x vals for tower types ', first, second, 'with n = ', n 
		x_vals = filter_xvals(encounters_json, filter_func)
		print 'found ', len(x_vals), 'values to plot'
		if len(x_vals) == 0:
			print 'did not find any x values to fit criterion'
			continue
		max_val, max_occurs = get_max_occurs(x_vals)
		y_axis = get_axis_range_for_max(max_occurs, axis_ranges)
		save_file = create_file_name(encounters_json, str(first), str(second), n, False)
		print 'creating graph to be stored at ', save_file
		create_dist_histogram(x_vals, bins, bin_range, y_axis,  save_file)
	return True

def create_graphs_on_times(encounters_json, destination_path, n, bins=150, bin_range=[0,180], use_majority=True, ignore_n=False):
	all_conditions = [isMorning,isHome,isNight]
	axis_ranges = [50, 200, 500, 1000, 2000, 5000]
	for first, second in itertools.permutations(all_conditions, 2):
		filter_func = create_times_filter_func(first,second, n, use_majority,ignore_n)
		print 'retreiving x vals for call times ', first.func_name, second.func_name, 'for n = ', n
		x_vals = filter_xvals(encounters_json, filter_func)
		print 'found ', len(x_vals), 'values to plot'
		if len(x_vals) == 0:
			print 'did not find any x values to fit criterion'
			continue
		max_val, max_occurs = get_max_occurs(x_vals)			
		y_axis = get_axis_range_for_max(max_occurs, axis_ranges)
		save_file = create_file_name(encounters_json, first.func_name, second.func_name, n, False)
		print 'creating graph to be stored at ', save_file
		create_dist_histogram(x_vals, bins, bin_range, y_axis,  save_file)
	return True

def create_loc_filter_func(first, second, n, towers_map,ignore_n=False):
	encs_count = 'encs_count'
	first_tower = 'first_tower'
	next_tower = 'next_tower'
	if ignore_n:
		return lambda row: (first in get_tower_code(row,first_tower, towers_map)) and (second in get_tower_code(row,next_tower,towers_map))
	else:
		return lambda row: (int(row[encs_count]) == n) and (first in get_tower_code(row,first_tower, towers_map)) and (second in get_tower_code(row,next_tower,towers_map))


def create_times_filter_func(first_cond,second_cond, n, use_majority=True, ignore_n=False):
	encs_count = 'encs_count'
	first_times = 'first_times'
	next_time = 'next_time'
	last_element = -1
	if ignore_n:
		if use_majority:
			return lambda row: majority_check(row[first_times],first_cond) and second_cond(row[next_time])
		else:
			return lambda row: first_cond(row[first_times][last_element]) and second_cond(row[next_time])
	else:
		if use_majority:
			return lambda row: (int(row[encs_count]) == n) and majority_check(row[first_times],first_cond) and second_cond(row[next_time])
		else:
			return lambda row: (int(row[encs_count]) == n) and first_cond(row[first_times][last_element]) and second_cond(row[next_time])


def create_encounters_count_filter(n,ignore_n=False):
	if ignore_n:
		return lambda row: (row['distance'] > 0)
	else:
		return lambda row: ((int(row['encs_count']) == n) and (row['distance'] > 0))

def create_friend_dist_graph(encounters_json, destination_path, n,  bins=100, bin_range=[0,100],ignore_n=False):
	filter_func = create_encounters_count_filter(n,ignore_n)
	print 'retreiving x vals for friend distance with n = ', n
	axis_ranges = [50, 200, 500, 1000, 2000, 5000]
	x_vals = graph_filter_vals(encounters_json, filter_func)
	print 'found ', len(x_vals), 'values to plot'
	if len(x_vals) == 0:
		print 'did not find any x values to fit criterion'
		return False
	max_val, max_occurs = get_max_occurs(x_vals)
	bin_range = [0, max_val]
	y_axis = get_axis_range_for_max(max_occurs, axis_ranges)
	save_file = create_file_name(encounters_json, None, None, n, True)
	print 'creating graph to be stored at ', save_file
	create_dist_histogram(x_vals, bins, bin_range, y_axis,  save_file)
	return True

def create_box_plot(encounter_json,save_file='../niquo_data/plots/box_plot_50.png',count=25):
	dist_vals = {}
	for line in open(encounter_json):
		row = json.loads(line)
		dist = row['distance']
		if dist < 0:
			continue
		n_val = row['encs_count']
		if (n_val not in dist_vals):
			dist_vals[n_val] = [dist]
		else:
			dist_vals[n_val].append(dist)

	keys = sorted(dist_vals.keys())[:count]
	transform = lambda d: '%d' % len(d)
	data = [dist_vals[n] for n in keys]
	tick_locs = range(1,)

	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax2 = ax1.twiny()


	ax1.boxplot(data)
	ax2.set_xlabel('Friendship Distance Distribution as a Function of Encounters Count')
	ax1.set_xlabel('Encounters Count')
	ax1.set_ylabel('User Friendship Distance')
	plt.xticks(range(1,count),keys)

	ax2.set_xlim(ax1.get_xlim())
	ax2.set_xticks(tick_locs)
	ax2.set_xticklabels([transform(v) for v in data])

	plt.savefig(save_file)
	return dist_vals


def generate_stats_per_tower(encounters_json,save_file='../niquo_data/filtered_data/lat_lon_median.csv'):
	encs_vals = {}
	tower_graph = nx.DiGraph()
	all_sources = set([])
	id_latlon = maps.id_to_lat_long()

	for line in open(encounters_json):
		row = json.loads(line)
		encs_count = row['encs_count']
		raw_distance = row['distance']
		lat_lon = id_latlon[row['first_tower'][10:-2]]
		lat_lon_other = id_latlon[row['next_tower'][10:-2]]
		delta_d = row['delta_days']
		delta_s = row['delta_seconds']
		delta_h = days_seconds_to_hours(int(delta_d),int(delta_s))

		if lat_lon not in all_sources:
			tower_graph.add_edge(lat_lon,lat_lon_other,weight=1)
			nx.set_edge_attributes(tower_graph,'times',{(lat_lon,lat_lon_other): [delta_h]})
			all_sources.add(lat_lon)
		else: 
			if lat_lon_other in tower_graph.neighbors(lat_lon):
				tower_graph.edge[lat_lon][lat_lon_other]['weight'] += 1
				tower_graph.edge[lat_lon][lat_lon_other]['times'].append(delta_h)
			else:
				tower_graph.add_edge(lat_lon,lat_lon_other,weight=1)
				nx.set_edge_attributes(tower_graph,'times',{(lat_lon,lat_lon_other): [delta_h]})
					
		if lat_lon not in encs_vals:
			encs_vals[lat_lon] = [encs_count]
		else:
			encs_vals[lat_lon].append(encs_count)

	with open(save_file, 'wb') as outfile:
		csvout = csv.writer(outfile,delimiter=',')
		first_row = ['latitude','longitude','median','mean']
		csvout.writerow(first_row)
		for lat_lon, all_encs in encs_vals.iteritems():
			lat = lat_lon[0]
			lon = lat_lon[1]
			med = np.median(all_encs)
			mean = np.mean(all_encs)
			tower_graph.node[lat_lon]['median_soc_dist'] = med
			tower_graph.node[lat_lon]['mean_soc_dist'] = mean
			csvout.writerow([lat,lon,med,mean])

	for source,dest in tower_graph.edges():
		tower_graph.edge[source][dest]['mean_hours'] = np.mean(tower_graph.edge[source][dest]['times'])
		tower_graph.edge[source][dest]['med_hours'] = np.median(tower_graph.edge[source][dest]['times'])

	return tower_graph



# *************HELPER FUNCTIONS*************

def get_max_occurs(x_vals):
	d = defaultdict(int)
	for i in x_vals:
		d[i] += 1
	return max(d.iteritems(), key=lambda x: x[1])


def create_file_name(json_filename, first, second, n, is_graph):
	dir_name = '/'.join(json_filename.split('/')[:-2]) + '/plots'
	suffix = '.png'
	if is_graph:
		filename = os.path.basename(json_filename)[:21] + '_' + 'DISTANCES' + '_N_' + str(n)
	else: 
		filename = os.path.basename(json_filename)[:21] + '_' + first + '_' + second + '_N_' + str(n)
	return os.path.join(dir_name, filename  + suffix)

def convert_row(row):
	days = int(row['delta_days'])
	seconds = int(row['delta_seconds'])
	return days_seconds_to_hours(days,seconds)

def get_tower_code(row,index,towers_map):
	# TODO: MAKE LESS HACKY
	# very hacky but only need it for this one number.
	try:
		return towers_map[row[index][10:-2]]
	except:
		return set([])

def get_axis_range_for_max(max_val, axis_ranges):
	for val in axis_ranges:
		if val > max_val:
			return val
	return max_val



def get_tower_types(towers_map):
	tower_codes = set([])
	for key,value in towers_map.iteritems():
		tower_codes = tower_codes.union(value)

	# manual clenaing
	if '' in tower_codes:
		tower_codes.remove('')
	if 'Category code' in tower_codes:
		tower_codes.remove('Category code')

	return list(tower_codes)

def majority_check(all_times,filter_func):
	check_times = up_encs.get_new_hours_encs(all_times)
	n = len(check_times)
	positive_vals = sum([1 for time_str in all_times if filter_func(time_str)])
	if (n % 2) == 0:
		return (positive_vals >= (n/2))
	else:
		return (positive_vals > (n/2))

def isMorning(time):
	return time_in_range(time,9,17)

def isHome(time):
	return time_in_range(time,20,24)

def isNight(time):
	return time_in_range(time,0,4)

def time_in_range(time,lower,upper):
	time_obj = get_time_obj(time)
	if (lower <= time_obj.hour < upper):
		return True
	return False

def time_obj_to_string(time_obj):
	format_string = "%Y.%m.%d %H:%M:%S"
	return time_obj.strftime(format_string)


def get_time_obj(time_string):
	format_string = "%Y.%m.%d %H:%M:%S"
	return datetime.strptime(time_string,format_string)

def create_time_string_from_delta(time,delta_d,delta_s):
	time_obj = get_time_obj(time)
	delta_obj = timedelta(int(delta_d),int(delta_s))
	new_obj = time_obj + delta_obj
	new_time = time_obj_to_string(new_obj)
	return new_time

def days_seconds_to_hours(days,seconds):
	total_secs = seconds + days*24*60*60
	total_hours = total_secs/(60*60)
	return total_hours

def create_dist_histogram(x_vals,bins, bin_range, y_axis, save_file):
	plt.hist(x_vals,bins,range=bin_range)
	plt.ylim([0, y_axis])
	plt.savefig(save_file)
	plt.clf()
	return True

def Main():
	encounters_json = '../niquo_data/v3_data_root/encounters_files/2016.07.01_2016.07.07_encounter.json'
	destination_path = '../niquo_data/v3_data_root/plots'

	create_graphs_on_times(encounters_json,destination_path,-1,150,[0,180],True,True)
	create_friend_dist_graph(encounters_json, destination_path, -1,  bins=100, bin_range=[0,100],ignore_n=True)
	create_graphs_on_tower_type(encounters_json, destination_path, -1, bins=150, bin_range=[0,180], ignore_n=True)

	for n in range(1,20):
		sub_dir = '/graphs_for_n_%d' % n
		dest_path = os.path.join(destination_path,sub_dir)
		print 'creating graphs for n =', n
		create_graphs_on_times(encounters_json, dest_path, n)
		print 'created graph for encounter times for n =', n
		create_friend_dist_graph(encounters_json, dest_path, n)
		print 'created friend distance graph for n = ', n
		create_graphs_on_tower_type(encounters_json, dest_path, n)
		print 'create tower type graph for n = ', n

	return True


if __name__ == '__main__':
    Main()