#!/usr/bin/env python

import numpy as np

import params as pr
import inputs as ip


def auxin_homeostasis(iton):
	
	'''
	Here implement: basal synthesis and turnover, possible effect of CUC on YUC,
	local modifications like exogenous application, etc
	A' = h * ( Synth + custom_synth_degr + C*k(CY) - A*k(Cdecay) )

	Params:
	* iton: Iteration of the simulation. This is used for local auxin synth/degr
	
	'''
	
	for y in range(ip.tissue_rows):
		for x in range(ip.tissue_columns):
			
			# Simplify var names
			auxin_cell = ip.auxin[y,x]
			cuc_cell = ip.cuc[y,x]
			h = pr.euler_h
			k_auxin_synth = pr.k_auxin_synth
			k_auxin_degr = pr.k_auxin_degr
			th_cuc_yuc1 = pr.th_cuc_yuc1
			k_cuc_yuc1 = pr.k_cuc_yuc1
			k_cuc_yuc4 = pr.k_cuc_yuc4

			# If current cell has local/custom auxin synth/degr...
			current_cell = (y,x)

			if current_cell in pr.auxin_custom_synth['cells'] and iton in pr.auxin_custom_synth['iterations']:
				local_synth = pr.auxin_custom_synth['value']
			else:
				local_synth = 0
			
			if current_cell in pr.auxin_custom_degr['cells'] and iton in pr.auxin_custom_synth['iterations']:
				local_degr = pr.auxin_custom_degr['value']
			else:
				local_degr = 0
			
			# Test: Effect of CUC on YUC1 follows a step function
			if cuc_cell >= th_cuc_yuc1:
				synth_yuc1 = cuc_cell * k_cuc_yuc1
			else:
				synth_yuc1 = 0
			
			# Calculate change in auxin concentration
			auxin_cell_updated = auxin_cell + h * ( \
				k_auxin_synth + \
				local_synth - \
				local_degr + \
				synth_yuc1 + \
				cuc_cell * k_cuc_yuc4 - \
				auxin_cell * k_auxin_degr \
			)
			
			if auxin_cell_updated < 0:
				auxin_cell_updated = 0
				
			ip.auxin[y,x] = auxin_cell_updated



def auxin_diffusion(h, k_auxin_diffusion, gridShape, tissue_columns, tissue_rows, auxin, fluxes, iteration):
	
	#
	# [auxin](i,j) = [auxin](i,j) - out_diff + in_diff_T + in_diff_R + in_diff_B + in_diff_L
	#
	# Rate of diffusion from cell i to j: dD(i->j)/dt = h * ( [auxin(i)] * k )
	#
	# k = diffusion factor constant
	#

	#fluxes = np.zeros(shape=(8,tissue_rows,tissue_columns)) # Z: T_out, T_in, R_out, R_in...

	for y in range(tissue_rows):
		for x in range(tissue_columns):
			
			# Top face
			if y > 0:
				T_out = h * ( auxin[y,x] * k_auxin_diffusion )
				T_in  = h * ( auxin[y-1,x] * k_auxin_diffusion )
			else:
				T_out, T_in = 0, 0

			# Right face
			if x < tissue_columns-1:
				R_out = h * ( auxin[y,x] * k_auxin_diffusion )
				R_in  = h * ( auxin[y,x+1] * k_auxin_diffusion )
			else:
				R_out, R_in = 0, 0

			# Bottom face
			if y < tissue_rows-1:
				B_out = h * ( auxin[y,x] * k_auxin_diffusion )
				B_in  = h * ( auxin[y+1,x] * k_auxin_diffusion )
			else:
				B_out, B_in = 0, 0

			# Left face
			if x > 0:
				L_out = h * ( auxin[y,x] * k_auxin_diffusion )
				L_in  = h * ( auxin[y,x-1] * k_auxin_diffusion )
			else:
				L_out, L_in = 0, 0

			fluxes[0,y,x] = T_out
			fluxes[1,y,x] = T_in
			fluxes[2,y,x] = R_out
			fluxes[3,y,x] = R_in
			fluxes[4,y,x] = B_out
			fluxes[5,y,x] = B_in
			fluxes[6,y,x] = L_out
			fluxes[7,y,x] = L_in

			# Calculate net fluxes (outbound) to draw vectors
			T_net_flux = T_out - T_in
			R_net_flux = R_out - R_in
			B_net_flux = B_out - B_in
			L_net_flux = L_out - L_in

			# Change sign of T and L net fluxes
			T_net_flux = - T_net_flux
			L_net_flux = - L_net_flux
			
			vector_x_component = L_net_flux + R_net_flux
			vector_y_component = T_net_flux + B_net_flux

			fluxes[8,y,x] = vector_x_component
			fluxes[9,y,x] = vector_y_component

	# Update the auxin concentrations after calculating all the fluxes to avoid polarity effect of looping through numpy array
	for y in range(tissue_rows):
		for x in range(tissue_columns):

			#auxin[x,y] = auxin[x,y] - (T_out + R_out + B_out + L_out) + (T_in + R_in + B_in + L_in)

			auxin[y,x] = auxin[y,x] - (fluxes[0,y,x] + fluxes[2,y,x] + fluxes[4,y,x] + fluxes[6,y,x]) + (fluxes[1,y,x] + fluxes[3,y,x] + fluxes[5,y,x] + fluxes[7,y,x])



def pin_on_auxin(h, auxin, pin1, k_pin1_transp, tissue_rows, tissue_columns, pin1_matrix_shape):

	#
	# PIN1-MEDIATED AUXIN TRANSPORT
	# Apply PIN1 transport to auxin concentration values
	#
	# PIN1_Tr = Nbr auxin molecules / ( PIN1 molecule * cycle )
	#
	# Transport rate = h * ( [auxin] * [PIN1] * k )
	#

	# Create absolute efflux transport values for each cell
	transpVectors = np.zeros(pin1_matrix_shape, dtype=(float,1)) # 3D array = (cell_face, column, row)
	
	for y in range(tissue_rows):
		for x in range(tissue_columns):

			auxin_molecules = auxin[y,x]
			total_pin1 = pin1[0,y,x] + pin1[1,y,x] + pin1[2,y,x] + pin1[3,y,x]
			transported_molecules_total = auxin_molecules * total_pin1 * k_pin1_transp
			
			#excess_ratio = transported_molecules_total / 

			# Manually limit transport if it exceeds the amount of auxin molecules
			# Later on: calculate excess ratio and then use to reduce the value of the vector below
			if transported_molecules_total > auxin_molecules:
				transported_molecules_total = auxin_molecules
				print('warning: transported molecules had to be manually adjusted in cell ' + str(y), str(x))

			# To top (y,x -> y-1,x)
			if y > 0:
				transpVectors[0,y,x] = h * ( auxin_molecules * pin1[0,y,x] * k_pin1_transp )
			else:
				transpVectors[0,y,x] = 0

			# To right (y,x -> y,x+1)
			if x < tissue_columns - 1:
				transpVectors[1,y,x] = h * ( auxin_molecules * pin1[1,y,x] * k_pin1_transp )
			else:
				transpVectors[1,y,x] = 0

			# To bottom (y,x -> y+1,x)
			if y < tissue_rows - 1:
				transpVectors[2,y,x] = h * ( auxin_molecules * pin1[2,y,x] * k_pin1_transp )
			else:
				transpVectors[2,y,x] = 0

			# To left (y,x -> y,x-1)
			if x > 0:
				transpVectors[3,y,x] = h * ( auxin_molecules * pin1[3,y,x] * k_pin1_transp )
			else:
				transpVectors[3,y,x] = 0

	for y in range(tissue_rows):
		for x in range(tissue_columns):

			# From top (y,x <- y-1,x)
			if y > 0:
				transpFromTop = transpVectors[2,y-1,x]
			else:
				transpFromTop = 0

			# From right (y,x <- y,x+1)
			if x < tissue_columns - 1:
				transpFromRight = transpVectors[3,y,x+1]
			else:
				transpFromRight = 0 

			# From bottom (y,x <- y+1,x)
			if y < tissue_rows - 1:
				transpFromBottom = transpVectors[0,y+1,x]
			else:
				transpFromBottom = 0

			# From left (y,x <- y,x-1)
			if x > 0:
				transpFromLeft = transpVectors[1,y,x-1]
			else:
				transpFromLeft = 0

			# Update the auxin concentration in each cell
			total_efflux = transpVectors[0,y,x] + transpVectors[1,y,x] + transpVectors[2,y,x] + transpVectors[3,y,x]
			auxin[y,x] = auxin[y,x] - total_efflux + transpFromTop + transpFromRight + transpFromBottom + transpFromLeft



if __name__ == '__main__':
    pass




