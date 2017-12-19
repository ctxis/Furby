#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  demo.py
#  
#  Copyright 2017 Ed Locard (@L0C4RD)
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  


from furby import dlc

########################################################################
#
# This demo is made to work with dlc TU003410.DLC.
# It builds the dlc we used in our demo video with Which?,
# which can be seen here: 
# https://www.which.co.uk/news/2017/12/connected-toys-buyers-beware-this-christmas/
#
########################################################################


def make_hacked_inverting(dlc_in="./dlc/dlc2/tu003410.dlc", left_gif="./images/demo_eyes/left.gif", right_gif="./images/demo_eyes/right.gif", dlc_out="./newdlc.dlc"):

	#Open, shrink audio.
	D = dlc(dlc_in)
	D.dlc_sections["AMF"].minify_audio()

	#Pop in exterminate audio (if you'd like.)
	#D.dlc_sections["AMF"].replace_track(138, "./your/audio/file1.a18")
	#D.dlc_sections["AMF"].replace_track(11, "./your/audio/file2.a18")

	#Two gifs here: a left gif, and a right gif.

	#Palettes.
	left_palette = D.dlc_sections["PAL"].extract_palette(left_gif)
	right_palette = D.dlc_sections["PAL"].extract_palette(right_gif)

	#Quarters.
	left_cels = D.dlc_sections["CEL"].quarterize(left_gif)
	right_cels = D.dlc_sections["CEL"].quarterize(right_gif)

	#Convenient transparent cel is currently at 0, leave it there.
	#Move convenient blank cell to cel 1. (It's currently at number 17.)
	blank_cel = []
	for y in range(64):
		for x in range(64):
			D.dlc_sections["CEL"].cels[1][y][x] = D.dlc_sections["CEL"].cels[17][y][x]

	#Get rid of all other cels.
	D.dlc_sections["CEL"].cels = D.dlc_sections["CEL"].cels[:2] + left_cels + right_cels

	#Overwrite palettes with our new palettes.
	victim_palette_L = 4 # chilli palette
	victim_palette_R = 5 # flame palette
	for i in range(len(D.dlc_sections["PAL"].palettes[victim_palette_L])):
		D.dlc_sections["PAL"].palettes[victim_palette_L][i] = left_palette[i]
	for i in range(len(D.dlc_sections["PAL"].palettes[victim_palette_R])):
		D.dlc_sections["PAL"].palettes[victim_palette_R][i] = right_palette[i]

	#Get existing palette offsets.
	existing_palettes = set()
	for f in D.dlc_sections["SPR"].frames:
		existing_palettes.update(f[1:8:2])
	existing_palettes = sorted(list(existing_palettes))
	#(eye palette is the first offset in this list)
	eye_palette = existing_palettes[0]
	#(chilli palette is the third offset in this list)
	chilli_palette = existing_palettes[2]
	#(flame palette is the fifth offset in this list)
	flame_palette = existing_palettes[4]

	#Replacing animations referenced in sequence 15. (75-0-4-4)
	#for i in range(3,11,2):
		#D.dlc_sections["SEQ"].sequences[15][i] = 0x8401
	D.dlc_sections["SEQ"].sequences[15][3] = 0x8401
	D.dlc_sections["SEQ"].sequences[15][4] = D.dlc_sections["SEQ"].entry_terminator
	D.dlc_sections["SEQ"].sequences[15] = D.dlc_sections["SEQ"].sequences[15][:5]

	#Replacing animations in sequence 50. (75-0-3-4)
	#for i in range(3,11,2):
		#D.dlc_sections["SEQ"].sequences[50][i] = 0x8401
	D.dlc_sections["SEQ"].sequences[50][3] = 0x8401
	D.dlc_sections["SEQ"].sequences[50][4] = D.dlc_sections["SEQ"].entry_terminator
	D.dlc_sections["SEQ"].sequences[50] = D.dlc_sections["SEQ"].sequences[50][:5]
	
	#Replacing animations in sequence 22. (75-0-0-3)
	#for i in range(3,15,2):
		#D.dlc_sections["SEQ"].sequences[22][i] = 0x8401
	D.dlc_sections["SEQ"].sequences[22][3] = 0x8401
	D.dlc_sections["SEQ"].sequences[22][4] = D.dlc_sections["SEQ"].entry_terminator
	D.dlc_sections["SEQ"].sequences[22] = D.dlc_sections["SEQ"].sequences[22][:5]

	#Remove eye frames, replace with white.
	for i in [8,9]:
		for f in D.dlc_sections["SPR"].frame_playlists[i]["frame_indices"]:
			
			D.dlc_sections["SPR"].frames[f][0] = 1 	# Blank white frame
			D.dlc_sections["SPR"].frames[f][2] = 1 	# Blank white frame
			D.dlc_sections["SPR"].frames[f][4] = 1 	# Blank white frame
			D.dlc_sections["SPR"].frames[f][6] = 1	# Blank white frame

			D.dlc_sections["SPR"].frames[f][1] = eye_palette
			D.dlc_sections["SPR"].frames[f][3] = eye_palette
			D.dlc_sections["SPR"].frames[f][5] = eye_palette
			D.dlc_sections["SPR"].frames[f][7] = eye_palette

	#Remove chilli frames, overwrite with white.
	for i in[10,11]:
		for f in D.dlc_sections["SPR"].frame_playlists[i]["frame_indices"]:
			
			D.dlc_sections["SPR"].frames[f][0] = 1 	# Blank white frame
			D.dlc_sections["SPR"].frames[f][2] = 1 	# Blank white frame
			D.dlc_sections["SPR"].frames[f][4] = 1 	# Blank white frame
			D.dlc_sections["SPR"].frames[f][6] = 1	# Blank white frame

			D.dlc_sections["SPR"].frames[f][1] = eye_palette
			D.dlc_sections["SPR"].frames[f][3] = eye_palette
			D.dlc_sections["SPR"].frames[f][5] = eye_palette
			D.dlc_sections["SPR"].frames[f][7] = eye_palette

	#Remove left-eye flames frames, overwrite with left-eye stuff.
	#frame 1 first:
	for f in D.dlc_sections["SPR"].frame_playlists[13]["frame_indices"][:10] + D.dlc_sections["SPR"].frame_playlists[13]["frame_indices"][19:29]:

		D.dlc_sections["SPR"].frames[f][0] = 2
		D.dlc_sections["SPR"].frames[f][2] = 3
		D.dlc_sections["SPR"].frames[f][4] = 4
		D.dlc_sections["SPR"].frames[f][6] = 5

		D.dlc_sections["SPR"].frames[f][1] = chilli_palette
		D.dlc_sections["SPR"].frames[f][3] = chilli_palette
		D.dlc_sections["SPR"].frames[f][5] = chilli_palette
		D.dlc_sections["SPR"].frames[f][7] = chilli_palette

	#frame 2 next:
	for f in D.dlc_sections["SPR"].frame_playlists[13]["frame_indices"][10:19] + D.dlc_sections["SPR"].frame_playlists[13]["frame_indices"][29:38]:

		D.dlc_sections["SPR"].frames[f][0] = 6
		D.dlc_sections["SPR"].frames[f][2] = 7
		D.dlc_sections["SPR"].frames[f][4] = 8
		D.dlc_sections["SPR"].frames[f][6] = 9

		D.dlc_sections["SPR"].frames[f][1] = chilli_palette
		D.dlc_sections["SPR"].frames[f][3] = chilli_palette
		D.dlc_sections["SPR"].frames[f][5] = chilli_palette
		D.dlc_sections["SPR"].frames[f][7] = chilli_palette

	#Remove right-eye flames frames, overwrite with right-eye stuff.
	#frame 1 first:
	for f in D.dlc_sections["SPR"].frame_playlists[12]["frame_indices"][:10] + D.dlc_sections["SPR"].frame_playlists[12]["frame_indices"][19:29]:

		D.dlc_sections["SPR"].frames[f][0] = 10
		D.dlc_sections["SPR"].frames[f][2] = 11
		D.dlc_sections["SPR"].frames[f][4] = 12
		D.dlc_sections["SPR"].frames[f][6] = 13

		D.dlc_sections["SPR"].frames[f][1] = flame_palette
		D.dlc_sections["SPR"].frames[f][3] = flame_palette
		D.dlc_sections["SPR"].frames[f][5] = flame_palette
		D.dlc_sections["SPR"].frames[f][7] = flame_palette
		
	for f in D.dlc_sections["SPR"].frame_playlists[12]["frame_indices"][10:19] + D.dlc_sections["SPR"].frame_playlists[12]["frame_indices"][29:38]:

		D.dlc_sections["SPR"].frames[f][0] = 14
		D.dlc_sections["SPR"].frames[f][2] = 15
		D.dlc_sections["SPR"].frames[f][4] = 16
		D.dlc_sections["SPR"].frames[f][6] = 17

		D.dlc_sections["SPR"].frames[f][1] = flame_palette
		D.dlc_sections["SPR"].frames[f][3] = flame_palette
		D.dlc_sections["SPR"].frames[f][5] = flame_palette
		D.dlc_sections["SPR"].frames[f][7] = flame_palette


	#Build it.
	D.build(dlc_out)
	return


if (__name__ == "__main__"):
	 make_hacked_inverting()
