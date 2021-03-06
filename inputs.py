#!/usr/bin/env python

import numpy as np

# === LOAD TEMPLATE DATA

# Templates

template = '2D'

auxin_template = 'templates/' + template + '/auxin_template'
pin1_template = 'templates/' + template + '/pin1_template'
cuc_template = 'templates/' + template + '/cuc_template'
middle_domain_template = 'templates/' + template + '/middle_domain_template'

auxin = np.loadtxt(auxin_template, delimiter=',', unpack=False)
auxin = auxin * 10
auxin_matrix_shape = auxin.shape
tissue_rows, tissue_columns = auxin.shape[0], auxin.shape[1]
pin1 = np.loadtxt(pin1_template, delimiter=',', unpack=False).reshape((4,tissue_rows,tissue_columns)) # Format is [z,y,x]
pin1_matrix_shape = pin1.shape
cuc = np.loadtxt(cuc_template, delimiter=',', unpack=False)
middle_domain = np.loadtxt(middle_domain_template, delimiter=',', unpack=False)

auxin_fluxes = np.zeros(shape=(8,tissue_rows,tissue_columns)) # Z: T_out, T_in, R_out, R_in...
#array_auxin_net_fluxes = np.zeros(shape=(2,tissue_rows,tissue_columns)) # where z[0] => dx and z[1] => dy

# LUTs
lut_auxin = np.loadtxt('luts/lut_red_sat.csv', delimiter=',', unpack=True, dtype=('int'), skiprows=1)
lut_pin1 = np.loadtxt('luts/lut_green.csv', delimiter=',', unpack=True, dtype=('int'), skiprows=1)
lut_cuc = np.loadtxt('luts/lut_green_sat.csv', delimiter=',', unpack=True, dtype=('int'), skiprows=1)