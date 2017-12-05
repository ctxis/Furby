#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  dlc.py
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

import struct
from PIL import Image as PILImage

class FormatError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class dlc(object):

	class dlcsection(object):

		def __init__(self, bytes_in=None):

			if (bytes_in is not None):
				self.rawbytes = str(bytes_in)
				self.cursor = 0
				self.length = len(bytes_in)
			else:
				self.rawbytes = ""
				self.cursor = 0
				self.length = 0
			
			#Set up per-subclass stuff.
			self.__initialise__()
			
			#Return content pointer if initialisation stuff has messed it up.
			self.__seek__(0)

		def __read__(self, numbytes):

			s = self.rawbytes[self.cursor:self.cursor+numbytes]
			self.cursor += len(s)
			return s

		def __seek__(self, pos):

			if (pos > self.length):
				raise IndexError("Cannot seek beyond end of bytes.")
				return None
			elif (pos < 0):
				raise IndexError("Cannot seek to a negative offset.")
				return None
			else:
				self.cursor = pos
				return self.cursor

		def __tell__(self):

			return self.cursor

		def __write__(self, bytes_in):
			
			t = type(bytes_in)
			if (t == list):
				for i in bytes_in:
					self.__write__(i)
			elif (t == str):
				self.rawbytes = self.rawbytes[:self.cursor] + bytes_in + self.rawbytes[self.cursor+len(bytes_in):]
				self.cursor += len(bytes_in)
			elif (t == int):
				self.rawbytes = self.rawbytes[:self.cursor] + chr(bytes_in) + self.rawbytes[self.cursor+len(bytes_in):]
				self.cursor += 1
			else:
				raise TypeError("Do not know how to write objects of type " + str(t))		

		def __unpack__(self, num_bytes=2):

			if (num_bytes == 1):
				return struct.unpack("<B", self.__read__(1))[0]
			elif (num_bytes == 2):
				return struct.unpack("<H", self.__read__(2))[0]
			elif (num_bytes == 4):
				return struct.unpack("<I", self.__read__(4))[0]
			else:
				raise TypeError("Unknown data type of length " + str(num_bytes))

		def __pack__(self, int_in, num_bytes=2):

			if (num_bytes == 1):
				self.__write__(struct.pack("<B", int_in))
			elif (num_bytes == 2):
				self.__write__(struct.pack("<H", int_in))
			elif (num_bytes == 4):
				self.__write__(struct.pack("<I", int_in))
			else:
				raise TypeError("Unknown data type of length " + str(num_bytes))

		def write_out(self, target=None):

			self.__compile__()
			
			#If no file handle supplied, simply return the string.
			if (target is None):
				return self.rawbytes

			#Otherwise, attempt to write to file handle.
			else:
				target.write(self.rawbytes)

		#Implement these per-class.
		def __compile__(self):
			raise NotImplementedError("Please implement a __compile__() for this section!")

		def __initialise__(self):
			raise NotImplementedError("Please implement an __initialise__() for this section!")

		def get_name(self):
			raise NotImplementedError("Please implement a get_name() for this section!")

	#Passes tests;
	#couple of weird magic values tho
	class HEADER_section(dlcsection):
		
		magic_bytes = ("\x00".join("FURBY")) + ("\x00" * 23) + ("\x78\x56\x34\x12\x02\x00\x08\x00")
		main_header_length = 0x288
		default_prefix = ("\x00".join("DLC_0000."))+ "\x00"
		weird_counter_initial_value = 0x0040cfb5
		section_entry_length = 38

		unknown_field = "???"
		header_fields = [unknown_field, "PAL", "SPR", "CEL", "XLS", unknown_field, unknown_field, unknown_field, unknown_field, "AMF", "APL", "LPS", "SEQ", "MTR", unknown_field, unknown_field]
		unused_fields = ["FIR", "FIT", "CMR", "INT"]
		
		def __initialise__(self):
			
			self.registered_fields = {}

			#If this section has been initialised with a non-zero string
			#of bytes, attempt to parse it.
			if (self.rawbytes != ""):

				#Check magic bytes.
				self.__seek__(0)
				try:
					assert(self.__read__(len(self.magic_bytes)) == self.magic_bytes)
				except:
					raise FormatError("Bad magic bytes.")
				
				#Find and read section information.
				num_section_entries, checknum = divmod((self.main_header_length - len(self.magic_bytes)), self.section_entry_length)
				try:
					assert (checknum == 0)
				except:
					raise FormatError("Bad Header Format.")

				for i in range(num_section_entries):
					thisrun = self.__read__(self.section_entry_length)
					
					if (thisrun[:len(self.default_prefix)] == self.default_prefix):
						section_name = thisrun[18:24:2]
						section_length = struct.unpack("<I", thisrun[30:34])[0]
						self.register_section(section_name, section_length)

				#And we're done!

		def __compile__(self):

			#Initialise.
			self.rawbytes = ""
			self.__seek__(0)

			#Start with the magic bytes.
			self.__write__(self.magic_bytes)

			#Next do the section references.
			weird_counter = self.weird_counter_initial_value

			for sec in self.header_fields:

				#If we haven't registered a particular section, just print a blank string of length 38d
				if sec not in self.registered_fields:
					self.__write__("\x00"*self.section_entry_length)

				#Otherwise, try to write out its section reference.
				else:
					
					self.__write__((self.default_prefix) + ("\x00".join(sec)) + ("\x00" * 3))
					self.__pack__(weird_counter, num_bytes=4)
					self.__pack__(self.registered_fields[sec], num_bytes=4)
					self.__write__("\x00" * 4)

					weird_counter += 0x1A
			
			#Once we've finished, we should make sure that the header length is exactly 0x288
			#(this seems to be important.)
			assert(len(self.rawbytes) == 0x288)

		#No get_name() because this is a strong independent header, it don't need no name

		#section_in should be a string
		#size should be an integer
		def register_section(self, section_in, size):

			if ((section_in in self.header_fields) and (section_in != self.unknown_field)):
				self.registered_fields[section_in] = size
			else:
				raise TypeError("We don't know how to build sections of type " + str(section_in))

		#List the order of sections in this file.
		def section_order(self):
			
			order = []
			
			for sec in self.header_fields:
				if sec in self.registered_fields:
					order.append(sec)
			
			return order

		#For research more than anything.
		def map_dlc(self):

			cursor = 0x288
			filemap = []
			for sec in self.header_fields:
				if sec in self.registered_fields:
					filemap.append((sec, self.registered_fields[sec], cursor))
					cursor += self.registered_fields[sec]
			
			return filemap

	#Passes tests;
	#All fields identified.
	class PAL_section(dlcsection):

		palette_size = 0x80
		num_colours = 64

		def __initialise__(self):

			self.palettes = []
			
			if (self.rawbytes != ""):
				
				num_palettes,leftover = divmod(len(self.rawbytes), self.palette_size)
				assert(leftover == 0)
				
				for pal in range(num_palettes):
					
					this_pal = []
					
					for _ in range(self.num_colours):
					
						single_colour = self.__unpack__(2)

						#Wacky 16-bit RGBA nonsense
						R = ((single_colour & 0b0111110000000000) >> 7)
						G = ((single_colour & 0b0000001111100000) >> 2)
						B = ((single_colour & 0b0000000000011111) << 3)
						A = ((single_colour & 0b1000000000000000) >> 8)

						if A == 0:
							A = 0xff
						else:
							A = 0

						this_pal.append((R,G,B,A))
					
					assert(len(this_pal) == self.num_colours)
					
					self.palettes.append(this_pal)

		def __compile__(self):

			self.rawbytes = ""
			self.__seek__(0)

			for p in self.palettes:
				for C in p:
					
					#Unpack into 16-bit RGBA.
					
					R = (C[0] & 0b11111000) << 7
					G = (C[1] & 0b11111000) << 2
					B = (C[2] & 0b11111000) >> 3
					A = 0b1000000000000000 if (C[3] == 0) else 0
					
					single_colour = R+G+B+A
					self.__pack__(single_colour, 2)

		def get_name(self):
			return "PAL"

		def extract_palette(self, filename_in):

			im = PILImage.open(filename_in)

			p = im.palette.getdata()

			if (p[0] == "RGB"):
				mypalette = [(
					ord(p[1][(3*i)]),
					ord(p[1][(3*i)+1]),
					ord(p[1][(3*i)+2]),
					0xff
				) for i in range(len(p[1])/3)]
			
			elif (p[0] == "RGBA"):
				mypalette = [(
					ord(p[1][(4*i)]),
					ord(p[1][(4*i)+1]),
					ord(p[1][(4*i)+2]),
					0 if (ord(p[1][(4*i)+3]) == 0) else 0xff
				) for i in range(len(p[1])/4)]
			else:
				raise NotImplementedError("Unsure how to handle palettes of type %s" % p[0])

			im.close()

			#Check length
			try:
				assert(len(mypalette) == self.num_colours)
			except AssertionError():
				raise FormatError("Palette is of length %d; need to use a single palette containing %d colours." % (len(my_palette), self.num_colours))
			else:
				return mypalette

	#Passes tests;
	#One weird byte left to identify.
	class SPR_section(dlcsection):

		t1_terminator = 0x40
		t3_terminator = 0xffff
		t1_length = 0xe0

		def __initialise__(self):

			self.frame_playlists = []
			self.frames = []
			
			if (self.rawbytes != ""):
				
				#Get type-1 entries.
				#[length of t2 entry, offset to t2 entry, ???(perhaps layer number?), terminator (0x40)]
				
				t2offsets = set()
				
				for w in range(16):

					raw_vals = [self.__unpack__(2), self.__unpack__(4), self.__unpack__(4), self.__unpack__(4)]
					
					assert(raw_vals[-1] == self.t1_terminator)
					
					self.frame_playlists.append({
						"framecount" 	:	raw_vals[0],
						"t2_offset_raw"	:	raw_vals[1],
						"layer" 	:	raw_vals[2],
						"t1_vals"  	:	raw_vals
					})
					
					t2offsets.add(raw_vals[1])

				#Get type-2 entries (pointers to whole frames)
				for w in range(16):
					self.__seek__(self.frame_playlists[w]["t2_offset_raw"]*2)
					self.frame_playlists[w]["t3_offsets_raw"] = [self.__unpack__(4) for _ in range(self.frame_playlists[w]["framecount"])]


				#Get type-3 entries (whole frames, as a sequence of quarter-frames)
				interim_frames = {}
				for w in range(16):
					for i in range(self.frame_playlists[w]["framecount"]):
						
						frame_offset = self.frame_playlists[w]["t3_offsets_raw"][i] 
						
						self.__seek__(frame_offset * 2)
						interim_frames[frame_offset] = [self.__unpack__(2) for _ in range(9)]
						assert(interim_frames[frame_offset][-1] == self.t3_terminator)

				#Build "frames", checking for missing/unreferenced frames.
				all_frame_offsets = list(range(self.t1_length/2, max(interim_frames)+1, 9))
				for i in all_frame_offsets:
					
					if i not in interim_frames:
						print "dead frame at index %02d" % i
						interim_frames[i] = [0,1,0,1,0,1,0,1,self.t3_terminator]

				self.frames = [interim_frames[i] for i in all_frame_offsets]

				#Fix up t3 indices.
				for w in range(16):
					self.frame_playlists[w]["frame_indices"] = [all_frame_offsets.index(i) for i in self.frame_playlists[w]["t3_offsets_raw"]]

				#Fix up t2 indices.
				t2offsets = sorted(list(t2offsets))
				for w in range(16):
					self.frame_playlists[w]["framelist_index"] = t2offsets.index(self.frame_playlists[w]["t2_offset_raw"])
				assert(set([w["framelist_index"] for w in self.frame_playlists]) == set(range(16)))


		def __compile__(self):

			self.rawbytes = ""
			self.__seek__(0)

			#build t3.
			t3_raw = ""
			for f in self.frames:
				for i in f:
					t3_raw += struct.pack("<H", i)

			#Fix up t3 offsets.
			word_offset, checknum = divmod(self.t1_length,2)
			assert(checknum == 0)
			for w in range(16):
				self.frame_playlists[w]["t3_offsets_raw"] = [ ((i * 9) + word_offset) for i in self.frame_playlists[w]["frame_indices"] ]

			#Fix up t2 offsets (and build t2.)
			t2_raw = ""
			word_offset, checknum = divmod((self.t1_length+len(t3_raw)),2)
			assert(checknum == 0)
			ordered_by_t2_index = sorted(range(len(self.frame_playlists)), key=lambda w : self.frame_playlists[w]["framelist_index"])
			for w in ordered_by_t2_index:
				self.frame_playlists[w]["t2_offset_raw"] = word_offset
				word_offset += 2 * len(self.frame_playlists[w]["frame_indices"])
				
				for i in self.frame_playlists[w]["t3_offsets_raw"]:
					t2_raw += struct.pack("<I", i)

			#Build t1.
			for w in range(16):
				self.__pack__(self.frame_playlists[w]["framecount"],2)
				self.__pack__(self.frame_playlists[w]["t2_offset_raw"],4)
				self.__pack__(self.frame_playlists[w]["layer"],4)
				self.__pack__(self.t1_terminator,4)

			#Lay down t3 (ffs Hasbro)
			self.__write__(t3_raw)

			#Lay down t2.
			self.__write__(t2_raw)

		def get_name(self):
			return "SPR"

		def analyse_frames(self, anim_no, frame_no):
			
			thisframe = self.anim_tree[anim_no]["frames"][frame_no]
			print [hex(i) for i in thisframe]

		def audit_palettes(self):

			palettes = set()

			for w in self.anim_tree:
				for f in self.anim_tree[w]["frames"]:
					for x in f[1::2]:
						palettes.add(x)
			
			print [hex(i) for i in palettes]

	#Passes tests;
	#All fields identified.
	class CEL_section(dlcsection):

		frame_length = 0xc00
		frame_width = 0x30	#	Thanks Jeija
		frame_height = 0x40	#	Thanks Jeija
		
		cel_width = 0x40
		cel_height = 0x40

		def __initialise__(self):

			self.cels = []

			#Make sure I haven't screwed up the maths
			assert(self.frame_height * self.frame_width == self.frame_length)
			assert(self.frame_length % 2 == 0)
			assert(self.frame_width % 3 == 0)

			#If this section has been initialised with a non-zero string
			#of bytes, attempt to parse it.
			if (self.rawbytes != ""):

				num_cels, cel_remainder = divmod(len(self.rawbytes), self.frame_length)

				try:
					assert(cel_remainder == 0)
				except:
					raise FormatError("Badly formed CEL section (length %d)" % len(self.rawbytes))

				#The cels section is pretty straightforward.
				#raw_cels = [self.rawbytes[i:(i+self.frame_length)] for i in range(0, len(self.rawbytes), self.frame_length)]
				for _ in range(num_cels):

					this_cel = []
					
					for row in range(self.frame_height):

						this_row = []
						
						#Yields four pixels per iteration.
						for column in range(self.frame_width/3):

							#Three bytes give four pixels.
							bytevals = [self.__unpack__(1) for i in range(3)]

							pixels = [
								(bytevals[0] >> 2),
								((bytevals[0] & 0x03) << 4 ) + (bytevals[1] >> 4),
								((bytevals[1] & 0x0f) << 2 ) + (bytevals[2] >> 6),
								(bytevals[2] & 0x3f)
							]

							for pixel in pixels:
								this_row.append(pixel)

						assert(len(this_row) == self.cel_width)
						this_cel.append(this_row)

					self.cels.append(this_cel)

		def __compile__(self):

			self.rawbytes = ""
			self.__seek__(0)

			#Pretty easy.
			for cel in self.cels:

				for row in range(self.cel_height):
					
					#four pixels are packed into three bytes.
					assert(len(cel[row]) == self.cel_width)
					for column in range(self.cel_width / 4):

						pixels = cel[row][(column*4):((column+1)*4)]
						
						bytevals = [
							(pixels[0] << 2) + (pixels[1] >> 4),
							((pixels[1] & 0x0f) << 4) + (pixels[2] >> 2),
							((pixels[2] & 0x03) << 6) + pixels[3]
						]

						for b in bytevals:
							self.__pack__(b, 1)


		def get_name(self):
			return "CEL"

		def draw_frame_greyscale(self, cel_number, filename_out):

			im = PILImage.new("RGB", (self.cel_width, self.cel_height), "white")

			cel = self.cels[cel_number]

			for y in range(self.cel_height):
				for x in range(self.cel_width):
					
					col = (cel[y][x]<<2,) * 3
					
					im.putpixel((x,y), col)

			im.save(filename_out)

		def quarterize(self, filename_in, demo_palette=None):

			quarters = []

			try:
				im = PILImage.open(filename_in)
				im.seek(0)
			except:
				return quarters

			while(True):

				w, h = im.size
				assert(w == (2*self.cel_width))
				assert(h == (2*self.cel_height))

				im_quarters = [[], [], [], []]
				im_x = [(0,w/2),(w/2,w),(0,w/2),(w/2,w)]
				im_y = [(0,h/2),(0,h/2),(h/2,h),(h/2,h)]


				for i in range(4):

					for y in range(im_y[i][0],im_y[i][1]):

						thisrow = []

						for x in range(im_x[i][0],im_x[i][1]):

							pix = im.getpixel((x,y))

							thisrow.append(pix)

						im_quarters[i].append(thisrow)

				if demo_palette is not None:

					for i in range(4):
						self.peek_image(im_quarters[i], demo_palette)

				for q in im_quarters:
					quarters.append(q)

				try:
					im.seek(im.tell()+1)
				except EOFError:
					break

			im.close()
			return quarters

		def peek_image(self, im_in, colourmap_in):

			h = len(im_in)
			w = len(im_in[0])

			im = PILImage.new("RGBA", (w,h))

			for y in range(h):
				for x in range(w):

					pix = im_in[y][x]
					col = colourmap_in[pix]

					im.putpixel((x,y), col)

			im.show()

		def analyse_colours(self, cel_no):
			
			cel = self.cels[cel_no]
			
			colours = set()
			
			for y in range(self.cel_height):
				for x in range(self.cel_width):
					colours.add(cel[y][x])

			print colours
			print hex(len(colours))

	#Passes tests;
	#several fields in the T3 and T4 entries in need of identification tho
	class XLS_section(dlcsection):

		default_header_entry_length = 0x03

		def __initialise__(self):
			self.action_tree = {}
			self.header_entry_length = self.default_header_entry_length

			#If this section has been initialised with a non-zero string
			#of bytes, attempt to parse it.
			if (self.rawbytes != ""):

				# Get first word. "Number of type-1 entries"
				type1_count = self.__unpack__(2)

				# Get length of type-1 entries (in words)
				self.header_entry_length = self.__unpack__(4)

				# Prepare to start moving through the tree, width-first (it's
				# inefficient, but cuts down the amount of seek()s we need to 
				# do, making the code a lot more straightforward to read.)

				# Start with type-1 entries.
				for i in range(1,type1_count+1):

					#The address of this particular entry.
					iaddress = self.__tell__()

					#The length of the type-2 entry this points to (in 6-byte entries)
					ilength = self.__unpack__(2)

					#The offset of that type2-entry (in words from the start of this section)
					ioffset = self.__unpack__(4)
					
					self.action_tree[i] = {
						"address"	:	iaddress,
						"points_at"	:	(2*ioffset),
						"entries"	:	ilength,
						"length"	:	(6*ilength)
					}

				# Now type-2 entries.
				for i in range(1,type1_count+1):
					
					self.__seek__(self.action_tree[i]["points_at"])
					for j in range(self.action_tree[i]["entries"]):

						#The address of this particular entry.
						jaddress = self.__tell__()

						#The length of the type-3 entry this points to (in 20-byte entries)
						jlength = self.__unpack__(2)

						#The offset of that type3-entry (in words from the start of this section) 
						joffset = self.__unpack__(4)
						
						self.action_tree[i][j] = {
							"address"	:	jaddress,
							"points_at"	:	(2*joffset),
							"entries"	:	jlength,
							"length"	:	(20*jlength)
						}


				# Next, type-3 entries.
				for i in range(1,type1_count+1):
					for j in range(self.action_tree[i]["entries"]):
						
						self.__seek__(self.action_tree[i][j]["points_at"])
						for k in range(self.action_tree[i][j]["entries"]):
							
							#The address of this particular entry.
							kaddress = self.__tell__()
							
							#kbamf = [ "{0:0{1}x}".format(self.__unpack__(1),2) for _ in range(20) ]
							kbamf = [
								self.__unpack__(2),	#often zero
								self.__unpack__(2),	#often 0x64 (100d)
								self.__unpack__(2),	#length of type-4 entry this points to (in 10-byte entries)
								self.__unpack__(4),	#The offset of that type-4 entry (in words from the start of this section)
								self.__unpack__(2),	#seems to be a small integer, [1:9]
								self.__unpack__(2),	#often zero
								self.__unpack__(2),	#often zero
								self.__unpack__(2),	#often zero
								self.__unpack__(2),	#often zero
							]
							
							#The length of the type-4 entry this points to (in 10-byte entries)
							#klength = int(''.join(kbamf[5:3:-1]), 16)
							klength = kbamf[2]
							
							#The offset of that type-4 entry (in words from the start of this section) 
							#koffset = int(''.join(kbamf[9:5:-1]), 16)
							koffset = kbamf[3]
							
							#Whether or not this is one of the nondefault callable DLC actions.
							#kcallable = (
								#kbamf[0:4] == ["00", "00", "64", "00"] and
								#kbamf[10:] == (["05"] + (["00"]*9))
							#)
							kcallable = (
								kbamf[0] == 0		and
								kbamf[1] == 0x64	and
								kbamf[4] == 5   	and
								kbamf[5] == 0   	and
								kbamf[6] == 0   	and
								kbamf[7] == 0   	and
								kbamf[8] == 0
							)

							self.action_tree[i][j][k] = {
								"address"	:	kaddress,
								"points_at"	:	(2*koffset),
								"entries"	:	klength,
								"length"	:	(10*klength),
								"callable"	:	kcallable,
								"raw"     	:	kbamf
							}


				# Finally, type-4 entries.
				for i in range(1,type1_count+1):
					for j in range(self.action_tree[i]["entries"]):
						for k in range(self.action_tree[i][j]["entries"]):

							self.__seek__(self.action_tree[i][j][k]["points_at"])
							for l in range(self.action_tree[i][j][k]["entries"]):

								#The address of this particular entry.
								laddress = self.__tell__()
								
								rawbytes = self.__read__(10)
								unboxing = struct.unpack("<HHHHH", rawbytes)
								
								self.action_tree[i][j][k][l] = {
									"address"	:	laddress,
									"rawbytes"	:	rawbytes,
									"bytes"		:	[hex(ord(b)) for b in rawbytes],
									"vals"		:	unboxing,
									"seq"		:	ord(rawbytes[0])
								}

		def __compile__(self):

			#Initialise.
			self.rawbytes = ""
			self.__seek__(0)

			#Work out the sizes of the type-1, -2, -3, and -4 sub-sections.
			#(please forgive the horrible one-liners)
			type1_len = 6 * (1 + len(self.action_tree))
			type2_len = sum([(6 * self.action_tree[i]["entries"]) for i in self.action_tree])
			type3_len = sum([sum([20 * self.action_tree[i][j]["entries"] for j in range(self.action_tree[i]["entries"])]) for i in self.action_tree])
			type4_len = sum([sum([sum([10 * self.action_tree[i][j][k]["entries"] for k in range(self.action_tree[i][j]["entries"])]) for j in range(self.action_tree[i]["entries"])]) for i in self.action_tree])

			#Prepopulate this section's content with zeroes (as we'll 
			#be hopping around quite a bit.)
			self.__write__("\x00" * sum([type1_len, type2_len, type3_len, type4_len]))
			self.__seek__(0)

			#Start with the "number of type-1 entries" word.
			self.__pack__(len(self.action_tree), 2)

			#Lay down the type-1 entries length dword.
			self.__pack__(self.header_entry_length, 4)

			#Start laying down type-1 entries.
			for i in self.action_tree:

				#The length of the type-2 entry this points to (in 6-byte entries)
				self.__pack__(self.action_tree[i]["entries"], 2)

				#The offset of that type2-entry (in words from the start of this section)
				self.__pack__((self.action_tree[i]["points_at"] >> 1), 4)

			#Now lay down type-2 entries.
			for i in self.action_tree:

				self.__seek__(self.action_tree[i]["points_at"])
				for j in range(self.action_tree[i]["entries"]):

					#The length of the type-3 entry this points to (in 20-byte entries)
					self.__pack__(self.action_tree[i][j]["entries"], 2)

					#The offset of that type2-entry (in words from the start of this section)
					self.__pack__((self.action_tree[i][j]["points_at"] >> 1), 4)

			#Next, lay down type-3 entries.
			for i in self.action_tree:
				for j in range(self.action_tree[i]["entries"]):
					
					self.__seek__(self.action_tree[i][j]["points_at"])
					for k in range(self.action_tree[i][j]["entries"]):
						
						 self.__pack__(self.action_tree[i][j][k]["raw"][0], 2)
						 self.__pack__(self.action_tree[i][j][k]["raw"][1], 2)
						 self.__pack__(self.action_tree[i][j][k]["raw"][2], 2)
						 self.__pack__(self.action_tree[i][j][k]["raw"][3], 4)
						 self.__pack__(self.action_tree[i][j][k]["raw"][4], 2)
						 self.__pack__(self.action_tree[i][j][k]["raw"][5], 2)
						 self.__pack__(self.action_tree[i][j][k]["raw"][6], 2)
						 self.__pack__(self.action_tree[i][j][k]["raw"][7], 2)
						 self.__pack__(self.action_tree[i][j][k]["raw"][8], 2)

			#Finally, lay down type-4 entries.
			for i in self.action_tree:
					for j in range(self.action_tree[i]["entries"]):
						for k in range(self.action_tree[i][j]["entries"]):

							self.__seek__(self.action_tree[i][j][k]["points_at"])
							for l in range(self.action_tree[i][j][k]["entries"]):
								
								self.__pack__(self.action_tree[i][j][k][l]["vals"][0], 2)
								self.__pack__(self.action_tree[i][j][k][l]["vals"][1], 2)
								self.__pack__(self.action_tree[i][j][k][l]["vals"][2], 2)
								self.__pack__(self.action_tree[i][j][k][l]["vals"][3], 2)
								self.__pack__(self.action_tree[i][j][k][l]["vals"][4], 2)


		def get_name(self):
			return "XLS"

	#Passes tests;
	#All fields identified.
	class AMF_section(dlcsection):

		a18_header = "\x00\xff\x00\xffGENERALPLUS SP\x00\x00"
		samplerate = 16000

		def __initialise__(self):
			self.tracks = []

			#If this section has been initialised with a non-zero string
			#of bytes, attempt to parse it.
			if (self.rawbytes != ""):

				#Get the number of tracks contained in't.
				track_count = self.__unpack__(4)

				#Get track offsets.
				track_offsets = []
				for _ in range(track_count):
					track_offsets.append(self.__unpack__(4))

				#Get tracks.
				for track_offset in track_offsets:
					self.__seek__(track_offset)
					
					lengthbytes = self.__read__(4)
					length = struct.unpack("<I", lengthbytes)[0]
					audiobytes = self.__read__(length)
					self.tracks.append(lengthbytes + audiobytes)	

		def __compile__(self):
			
			#Initialise.
			self.rawbytes = ""
			self.__seek__(0)

			#Start with the "number of entries" dword.
			self.__pack__(len(self.tracks), 4)
			
			#work out offset to first track
			offset_to_next_track = 4 * (1 + len(self.tracks))
			
			#section header: write offsets to each track.
			for t in self.tracks:
				
				self.__pack__(offset_to_next_track, 4)
				offset_to_next_track += len(t)

			#Lastly, write out the tracks proper.
			for t in self.tracks:
				self.__write__(t)

		def get_name(self):
			return "AMF"

		def __get_track__(self, trackpath):

			with open(trackpath, "r") as f:

				#Check for generalplus header; remove if found.
				firstbytes = f.read(len(self.a18_header))
				if (firstbytes == self.a18_header):
					f.seek(0x30)
				else:
					f.seek(0x00)

				lengthbytes = f.read(4)
				filelength = struct.unpack("<I", lengthbytes)[0]
				audiobytes = f.read(filelength)

			return lengthbytes + audiobytes

		def add_track(self, trackpath, pos=None):

			newbytes = self.__get_track__(trackpath)

			if (pos is None):
				self.tracks.append(newbytes)
				return len(self.tracks) -1

			elif (pos >= len(self.tracks)):
				self.tracks.append(newbytes)
				return len(self.tracks) -1

			elif (pos < 0):
				self.tracks.insert(0, newbytes)
				return 0

			else:
				self.tracks.insert(pos, newbytes)
				return pos


		def remove_track(self, track_number):
			return self.tracks.pop(track_number)

		def replace_track(self, tracknumber, trackpath):

			self.remove_track(tracknumber)
			self.add_track(trackpath, tracknumber)

		def minify_audio(self, newlength_in=128):

			#This always needs to be a multiple of 8.
			audio_length = ((newlength_in  >> 3 ) << 3)
			sampling_length = 2
			size_length = 4
			
			newlength_packed = struct.pack("<I", audio_length + sampling_length)
			sample_rate = struct.pack("<H", self.samplerate)
			
			for i in range(len(self.tracks)):
				
				newtrack = newlength_packed + sample_rate + self.tracks[i][6:6+audio_length]
				self.tracks[i] = newtrack

	#Passes tests;
	#All fields identified.
	class APL_section(dlcsection):

		default_major_offset = 0x4000	# needed by the SEQ section
		default_minor_offset = 0x546
		
		entry_terminator = 0xf000

		#length of an individual entry in the section header, in bytes.
		default_header_entry_length = 0x04

		def __initialise__(self):
			self.playlists = []
			self.header_entry_length = self.default_header_entry_length

			#If this section has been initialised with a non-zero string
			#of bytes, attempt to parse it.
			if (self.rawbytes != ""):

				#Get the number of playlists contained in't.
				playlist_count = self.__unpack__(2)

				#Get the next word (possibly memory address into which these playlists will be copied.
				memloc = self.__unpack__(2)
				assert (memloc - self.default_minor_offset == playlist_count)

				#Get header entry length.
				self.header_entry_length = self.__unpack__(4)

				#Get playlist offsets.
				playlist_offsets = [(2 * self.__unpack__(4)) for _ in range(playlist_count)]

				#Make categorizer.
				cat = lambda w: (w, "EOF") if (w == self.entry_terminator) else (w, "PAUSE") if (w & 0x1000 == 0x1000) else (w, "AUDIO")

				#Get playlists.
				for playlist_offset in playlist_offsets:

					self.__seek__(playlist_offset)

					this_playlist = [cat(self.__unpack__(2))]
					
					while (this_playlist[-1][1] != "EOF"):
						this_playlist.append(cat(self.__unpack__(2)))

					self.playlists.append(this_playlist)


		def __compile__(self):
			#Initialise.
			self.rawbytes = ""
			self.__seek__(0)

			#Start with the "number of entries" word.
			self.__pack__(len(self.playlists), 2)

			#Unsure how this value is used, but it appears to be the number of entries plus 0x546
			self.__pack__(len(self.playlists)+self.default_minor_offset, 2)

			#Header entry length (seems to normally be 4.)
			self.__pack__(self.header_entry_length, 4)

			#work out offset to first playlist
			offset_to_next_playlist = 2 * (2 + len(self.playlists))
			
			#section header: write offsets to each playlist.
			for pl in self.playlists:
				
				self.__pack__(offset_to_next_playlist, 4)
				offset_to_next_playlist += len(pl) # This is 2 * (0.5 * len(pl))

			#Lastly, write out the playlists proper.
			for pl in self.playlists:
				for e in pl:
					self.__pack__(e[0], 2)

		def get_name(self):
			return "APL"

		def add_playlist(self, pl_in):
			
			#verify.
			try:
				#1: even number of entries.
				assert(len(pl_in) % 2 == 0)
				
				#2: all values >= 0.
				assert(all(i>=0 for i in pl_in))

				#3: every second value is a pause. Can't be greater than 0x2000.
				assert(all(i<0x2000 for i in pl_in[1:-1:2]))

				#4: last value is the entry terminator.
				assert(pl_in[-1] == self.entry_terminator)
				
				#5: none of the other values are the entry terminator.
				assert(all(i<self.entry_terminator for i in pl[0:-2:2]))
			except:
				raise FormatError("Invalid playlist description.")
			else:
				self.playlists.append(list(pl_in))

	#Passes tests;
	#Need to identify entry words (looks like 0x8xxx is "open mouth" and 0x1xxx is "shut mouth")
	class LPS_section(dlcsection):

		default_header_entry_length = 0x03
		header_terminator = 0xffffffff
		entry_terminator = 0xffff

		def __initialise__(self):
			
			self.phrases = []
			self.header_entry_length = self.default_header_entry_length
			
			if (self.rawbytes != ""):

				#Get the number of phrases contained in't.
				phrase_count = self.__unpack__(2)

				#Get header entry length.
				self.header_entry_length = self.__unpack__(4)

				#Get phrase offsets.
				phrase_offsets = [(2 * (3 + self.__unpack__(4))) for _ in range(phrase_count)]
				
				#Check for terminator.
				assert(self.__unpack__(4) == self.header_terminator)

				#Get animations.
				for phrase_o in phrase_offsets:

					self.__seek__(phrase_o)
					this_phrase = [self.__unpack__(2)]
					
					while (this_phrase[-1] != self.entry_terminator):
						this_phrase.append(self.__unpack__(2))
				
					self.phrases.append(this_phrase)

		def __compile__(self):

			#Initialise.
			self.rawbytes = ""
			self.__seek__(0)

			#Start with the "number of entries" word.
			self.__pack__(len(self.phrases), 2)

			#Header entry length (seems to normally be 3.)
			self.__pack__(self.header_entry_length, 4)

			#work out offset to first phrase
			offset_to_next_phrase =  2 * (1 + len(self.phrases))
			
			#section header: write offsets to each phrase.
			for phrase in self.phrases:

				self.__pack__(offset_to_next_phrase, 4)
				offset_to_next_phrase += len(phrase)

			#write header terminator
			self.__pack__(self.header_terminator, 4)

			#Lastly, write out each phrase.
			for phrase in self.phrases:
				for p in phrase:
					self.__pack__(p, 2)

		def get_name(self):
			return "LPS"

	#Passes tests,
	#need to deconstruct SEQ entries tho
	class SEQ_section(dlcsection):

		default_header_entry_length = 0x06	# in bytes
		entry_terminator = 0

		def __initialise__(self):
			self.sequences = []
			self.header_entry_length = self.default_header_entry_length

			#If this section has been initialised with a non-zero string
			#of bytes, attempt to parse it.
			if (self.rawbytes != ""):

				#Get the number of sequences contained in't.
				seq_count = self.__unpack__(2)

				#Get header entry length.
				self.header_entry_length = self.__unpack__(4)

				#Get sequence offsets.
				seq_offsets = [(2 * self.__unpack__(4)) for _ in range(seq_count)]

				#Get sequences.
				for seq_o in seq_offsets:

					self.__seek__(seq_o)
					this_sequence = [self.__unpack__(2)]
					
					#First word: 0x02 or 0x03
					#Second word: Playlist select.
					#Third word: MTR select (or pick one of the actions pre-programmed on the furby; first nibble determines which)
					#Fourth -> (n-1)th word: Eye animation select. Every second word indicates inter-animation delay.
					while (this_sequence[-1] != self.entry_terminator):
						this_sequence.append(self.__unpack__(2))
				
					self.sequences.append(this_sequence)

		def __compile__(self):

			#Initialise.
			self.rawbytes = ""
			self.__seek__(0)

			#Start with the "number of entries" word.
			self.__pack__(len(self.sequences), 2)

			#header entry length.
			self.__pack__(self.header_entry_length, 4)

			#work out offset to first sequence
			offset_to_next_sequence = (2 * (1 + len(self.sequences))) + 1
			
			#section header: write offsets to each playlist.
			for seq in self.sequences:

				self.__pack__(offset_to_next_sequence, 4)
				offset_to_next_sequence += len(seq) # This is 2 * (0.5 * len(pl))

			#Lastly, write out the sequences proper.
			for seq in self.sequences:
				for e in seq:
					self.__pack__(e, 2)

		def get_name(self):
			return "SEQ"

	#Passes tests,
	#need to deconstruct MTR entries tho
	class MTR_section(dlcsection):

		default_header_entry_length = 0x03
		entry_terminator = 0xf000

		def __initialise__(self):
			
			self.animations = []
			self.header_entry_length = self.default_header_entry_length
			
			if (self.rawbytes != ""):

				#Get the number of animations contained in't.
				anim_count = self.__unpack__(2)

				#Get header entry length.
				self.header_entry_length = self.__unpack__(4)

				#Get animation offsets.
				anim_offsets = [(2 * (3 + self.__unpack__(4))) for _ in range(anim_count)]

				#Get animations.
				for anim_o in anim_offsets:

					self.__seek__(anim_o)
					this_anim = [self.__unpack__(2)]
					
					while (this_anim[-1] != self.entry_terminator):
						this_anim.append(self.__unpack__(2))
				
					self.animations.append(this_anim)

		def __compile__(self):

			#Initialise.
			self.rawbytes = ""
			self.__seek__(0)

			#Start with the "number of entries" word.
			self.__pack__(len(self.animations), 2)

			#Header entry length (seems to normally be 3.)
			self.__pack__(self.header_entry_length, 4)

			#work out offset to first animation
			offset_to_next_animation = 2 * len(self.animations)
			
			#section header: write offsets to each animation.
			for anim in self.animations:

				self.__pack__(offset_to_next_animation, 4)
				offset_to_next_animation += len(anim)

			#Lastly, write out the playlists proper.
			for anim in self.animations:
				for a in anim:
					self.__pack__(a, 2)

		def get_name(self):
			return "MTR"

	#Creates the class.
	#Also includes a self-test - to run it, just set self_test to something.
	def __init__(self, filepath_in=None, self_test=None):

		self.dlc_header = None
		self.dlc_sections = {}

		if filepath_in is not None:

			with open(filepath_in, "r") as f:

				#Parse header.
				self.dlc_header = self.HEADER_section(f.read(0x288))

				#Map sections
				section_map = self.dlc_header.map_dlc()

				filemap = { e[0] : {"l" : e[1], "o" : e[2]} for e in section_map}
				
				#Generate section objects.
				section_generators = {
					"PAL"   	:	self.PAL_section,
					"SPR"   	:	self.SPR_section,
					"CEL"   	:	self.CEL_section,
					"XLS"   	:	self.XLS_section,
					"AMF"   	:	self.AMF_section,
					"APL"   	:	self.APL_section,
					"LPS"   	:	self.LPS_section,
					"SEQ"   	:	self.SEQ_section,
					"MTR"   	:	self.MTR_section,
				}

				for sec in filemap:

					f.seek(filemap[sec]["o"])
					rawbytes = f.read(filemap[sec]["l"])

					d = section_generators[sec](rawbytes)
					
					self.dlc_sections[sec] = d
					
					if (self_test is not None):

						print "testing %s at offset %d" % (sec, filemap[sec]["o"])
						newbytes = d.write_out()
						try:
							print(len(rawbytes) == len(newbytes))
							assert(rawbytes == newbytes)
						except:
							i=0
							for i in range(min(len(rawbytes), len(newbytes))):
								if rawbytes[i] != newbytes[i]:
									break
							raise AssertionError("Test failed: error at offset 0x%x\n\texpected %02x, got %02x" % (i, ord(rawbytes[i]), ord(newbytes[i]) ))
						else:
							print "\tTest Successful!"

	#Builds a new DLC.
	def build(self, filepath_in):

		#Generate each of the sections we'd like to include.
		#Also re-generate the header as we go.
		self.dlc_header.registered_fields = {}
		generated_sections = {}
		for sec in self.dlc_header.header_fields:
			if sec in self.dlc_sections:
				generated_sections[sec] = self.dlc_sections[sec].write_out()
				self.dlc_header.register_section(sec, len(generated_sections[sec]))

		#Open the file.
		with open(filepath_in, "w") as f:

			#Write header.
			f.write(self.dlc_header.write_out())
			
			#Try to write out each section.
			for sec in self.dlc_header.header_fields:
				if sec in self.dlc_sections:
					f.write(self.dlc_sections[sec].write_out())

	def draw_cel(self, cel_number, pal_number, outfile):

		target_cel = self.dlc_sections["CEL"].cels[cel_number]
		target_palette = self.dlc_sections["PAL"].palettes[pal_number]
		
		w = self.dlc_sections["CEL"].cel_width
		h = self.dlc_sections["CEL"].cel_height
		
		im = PILImage.new("RGBA", (w, h))

		for y in range(h):
			for x in range(w):
				
				col_index = target_cel[y][x]
				
				true_col = target_palette[col_index]

				im.putpixel((x,y), true_col)

		#Use PNGs to preserve transparency.
		im.save(outfile, format="PNG")

	def dump_images(self, palette_number, stub="./cel%04d.png"):

		for p in range(len(self.dlc_sections["CEL"].cels)):

			self.draw_cel(p, palette_number, (stub % p))

