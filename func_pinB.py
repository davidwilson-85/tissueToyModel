#!/usr/bin/env python

import numpy as np
import math


def pin_expression(pin1, auxin, cuc, k_auxin_pin1, k_cuc_pin1, k_pin1_decay):

	'''
	* Auxin promotes PIN1 expression.
	* ChCUC1 promoted PIN1 expression.
	
	To model this, assume that auxin and CUCs increase PIN1 expression and PIN1 has a constant turnover/decay
	
	P' = h * ( A*P*K(AP) + C*P*K(CP) - P*K(Pdecay) )

	'''

	
	for y in range(auxin.shape[0]):
		for x in range(auxin.shape[1]):
		
			pin1_cell = pin1[0,y,x] + pin1[1,y,x] + pin1[2,y,x] + pin1[3,y,x]
			auxin_cell = auxin[y,x]
			cuc_cell = cuc[y,x]
			
			pin1_cell_updated = pin1_cell + h * ( auxin_cell * pin1_cell * k_auxin_pin1 + cuc_cell * pin1_cell * k_cuc_pin1 - pin1_cell * k_pin1_decay )
			
			if pin1_cell_updated < 0:
				pin1_cell_updated = 0
			
			pin1_ratio = float(pin1_cell_updated / pin1_cell)
			
			pin1[0,y,x] = pin1[0,y,x] * pin1_ratio
			pin1[1,y,x] = pin1[1,y,x] * pin1_ratio
			pin1[2,y,x] = pin1[2,y,x] * pin1_ratio
			pin1[3,y,x] = pin1[3,y,x] * pin1_ratio


def pin_polarity(auxin, pin1, k_UTG, cuc, cuc_threshold_pin1):

	"""
	Default PIN1 polarity mode is UTG
	CUC genes affect PIN1 subcellular localization
	It is not clear how. Test different hypotheses (WTF, reversal, non-polar, DTCG, UTG dampening, etc...)
	
	"""

	for y in range(auxin.shape[0]):
		for x in range(auxin.shape[1]):

			if int(cuc[y,x]) > cuc_threshold_pin1:
				#pin_wtf_p(auxin_fluxes, pin1[:,y,x], k_WTF)
				pass
			else:
				pin_utg_smith2006(y, x, auxin, pin1[:,y,x], k_UTG)



def pin_utg_smith2006(y, x, auxin, pin1, k_UTG):

	#
	# Auxin affect PIN1 subcellular localization (up-the-gradient model = UTG)
	# UTG: PIN1 accumulates at membrane abutting cells with higher auxin concentration
	# 
	# I use formula from Smith 2006 (also used in Bilsborough 2011):
	#
	#                                    b^A[i]
	# PIN[ij] (potential) = PIN[i] * ---------------
	#                                 SUM[k] b^A[k] 
	#
	# Current problem: As it is now, function does not take into account current PIN1 distribution, so it erases any initial
	# state defined in the template
	
	# Base of exponential function to tweak with UTG responsiveness
	b = k_UTG
	
	# Current PIN1 total amount in the cell
	total_pin1 = pin1[0] + pin1[1] + pin1[2] + pin1[3]

	# Calculate auxin in neighbours (correcting in boundary cells)
	# Top
	if y > 0:
		auxin_top = auxin[y-1,x]
	else:
		auxin_top = auxin[y,x]
	
	# Right
	if x < auxin.shape[1] - 1:
		auxin_right = auxin[y,x+1]
	else:
		auxin_right = auxin[y,x]
	
	# Bottom
	if y < auxin.shape[0] - 1:
		auxin_bottom = auxin[y+1,x]
	else:
		auxin_bottom = auxin[y,x]
	
	# Left
	if x > 0:
		auxin_left = auxin[y,x-1]
	else:
		auxin_left = auxin[y,x]

	# Calculate normalization factor (eq. denominator)
	norm_factor = b**auxin_top + b**auxin_right + b**auxin_bottom + b**auxin_left

	# Calculate PIN1 alocation at each cell face
	pin1[0] = total_pin1 * ( b**auxin_top / norm_factor )
	pin1[1] = total_pin1 * ( b**auxin_right / norm_factor )
	pin1[2] = total_pin1 * ( b**auxin_bottom / norm_factor )
	pin1[3] = total_pin1 * ( b**auxin_left / norm_factor )

	#print pin1[0,y,x], pin1[1,y,x], pin1[2,y,x], pin1[3,y,x]	
	#print utg_auxinRatioT, utg_auxinRatioR, utg_auxinRatioB, utg_auxinRatioL



def pin_wtf_p(auxin_fluxes, pin1, k_WTF):

	# 
	# Calculation similar to UTG (Smith2006) but using passive (p) net flux to allocate PIN1 instead of nighbour auxin concentrations.
	# 
	# Try using the net flux VS only the efflux

	# Base of exponential function to tweak with UTG responsiveness
	b = k_WTF
	
	for y in range(auxin_fluxes.shape[1]):
		for x in range(auxin_fluxes.shape[2]):
		
			# Current PIN1 total amount in the cell
			total_pin1 = pin1[0,y,x] + pin1[1,y,x] + pin1[2,y,x] + pin1[3,y,x]
	
			# Calculate net flux at each cell face
			netflux_top = auxin_fluxes[0,y,x] - auxin_fluxes[1,y,x]
			netflux_right = auxin_fluxes[2,y,x] - auxin_fluxes[3,y,x]
			netflux_bottom = auxin_fluxes[4,y,x] - auxin_fluxes[5,y,x]
			netflux_left = auxin_fluxes[6,y,x] - auxin_fluxes[7,y,x]

			'''
			if y == 1 and x == 1:
				print(auxin_fluxes[4,y,x], auxin_fluxes[5,y,x])
				print(netflux_top, netflux_right, netflux_bottom, netflux_left)
				print('')
			'''
			
			# Calculate normalization factor (eq. denominator)
			norm_factor = b**netflux_top + b**netflux_right + b**netflux_bottom + b**netflux_left
			
			# Calculate new PIN amount at each cell face
			pin1[0,y,x] = total_pin1 * ( b**netflux_top / norm_factor )
			pin1[1,y,x] = total_pin1 * ( b**netflux_right / norm_factor )
			pin1[2,y,x] = total_pin1 * ( b**netflux_bottom / norm_factor )
			pin1[3,y,x] = total_pin1 * ( b**netflux_left / norm_factor )


def pin1_dual_pol():

	# 
	# UTG and WTF modes coexist. Default mode is UTG. CUC presence in cell favours WTF.
	# 
	# 
	# 
	# 
	# 

	pass





if __name__ == '__main__':
    pass

