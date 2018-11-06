#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Utility
#Clean some headers in fits files
#Input:list of fits files
#Output:the same files cleaned 
#config file parameters:
#	Section:[CLEANHEADER]
#		keepheader
#Nacho Mas Junio 2013
#Status: work

import pyfits
import commands,os, sys
from eUconfig import *

cfg=dict(config.items("CLEANHEADER"))
KEEPheader=cfg["keepheader"]

class headerCleaner:

	def do(self,argu):
		for arg in argu:
			print ""	
        		print "CLEANING HEADER FITS:",arg
			#filename=os.path.splitext(arg)[0]
			hdulist = pyfits.open(arg,mode='update')
			#hdulist.info()
			header=hdulist[0].header
			for key in header.keys():
				if not key in KEEPheader:
					print "Deleting ",key
					del header[key]
			#print header
			hdulist.close()
		return 

	


if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	cleaner=headerCleaner()
	cleaner.do(fitsFiles)




