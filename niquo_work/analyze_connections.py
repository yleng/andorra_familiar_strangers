import cPickle
import csv
import os
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import crossing_paths as cp
import extractData as ex

def get_encounters_count(enc_map):
	all_counts = []
	for caller, receiver_dict in enc_map.iteritems():
		for receiver, occurances in receiver_dict.iteritems():
			all_counts.append(len(occurances))
	print 'found', len(all_counts),'encounters.'
	return all_counts

def get_entire_distribution(enc_maps_path):
	all_encounters_count = []
	all_dates = os.listdir(enc_maps_path)
	print 'checking', len(all_dates),'date files'
	for date in all_dates:
		date_dir = enc_maps_path + date
		all_towers = os.listdir(date_dir)
		print 'checking', len(all_towers),'for date', date
		for tower_map in all_towers:
			tower_path = date_dir + '/' + tower_map
			enc_map = cPickle.load(open(tower_path,'rb'))
			print 'finding all counts for', tower_path
			all_encounters_count.append(get_encounters_count(enc_map))
	return np.array(all_encounters_count)

def filter_produce_hist(file_path,save_path,filter_func=lambda x: True):
	days_row = 2
	all_rows = ex.read_csv(file_path,float('inf'))
	x_vals = [row[days_row] for row in all_rows if filter_func(row)]

	filename =  file_path.split('/')[-1].split('.')[0] + '.png'
	create_dist_histogram(x_vals,save_path + filename)
	return True

def create_dist_histogram(x_vals,save_file):
	plt.hist(x_vals)
	plt.savefig(save_file)
	return True

def first_encountered_after_hour():
	return True

def encountered_on_weekends():
	return True




