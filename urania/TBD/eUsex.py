#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#Sextract sources from fits files for futher processing
#Input:list of fits files
#Output:same names but with 'cat' file extension
#config file parameters:
#
#	Section:[SEXFAST] or [SEXASTEROIDS]
#		sexcfg
#		sexparam
#		sexfilter
#		sigma
#Nacho Mas Junio 2013
#Status: work for La Sagra file

import pyfits
import math
import commands,os, sys

from eUconfig import *


class sextractor(helper):
	def do(self,section):
	 cfg=dict(config.items(section))
	 for i,arg in enumerate(self.solvefits):
		print ""	
	        print "FILE:",arg
		filename=self.catalogs[i]
	        #meto una nueva columna con la fecha de la observacion
		hdulist = pyfits.open(arg,mode='update')
		hdr = hdulist[0].header
		try:
		        date=hdr['DATE-OBS']
		except:
			try:
				date=hdr['DATE']
			except:
				print "FITS NOT CONTAING DATE/DATE-OBS KEY"
				exit(0)

		try:
		        ZP=hdr['ZMAG']
		except:
			try:
				ZP=hdr['ZEROPOINT']
			except:
				ZP=float(cfg['default_zeropoint'])
				print "FITS NOT CONTAING ZMAG/ZEROPOINT KEY"
				print "Using defaults:"	+str(ZP)
	
		try:
		        GAIN=hdr['EGAIN']
		except:
			try:
				GAIN=hdr['GAIN']
			except:
				print "FITS NOT CONTAING GAIN/EGAIN KEY"
				GAIN=1

	        print self.exposure
		ZP=ZP+2.5*math.log10(self.exposure)
		print "SETTING ZP",ZP,2.5*math.log10(self.exposure)
		print "SETTING MJDATE OBS DATE:",arg,date

        	hdulist.close()
        	#FITS_1.0 
		#filter  Cuando mas pequeño mas detecciones. No se puede quitar porque entonces las detecciones se disparan
		#Es muy importante!!!
		#el que mejor cuadra con la sagra es tophat 2.0 3x3
	
		sexStr="sex "+arg+" -c "+cfg["sexcfg"]+" -CATALOG_NAME "+filename+" -FILTER Y -FILTER_NAME "+cfg["sexfilter"]+ \
		" -CATALOG_TYPE FITS_1.0  " +" -PARAMETERS_NAME "+cfg["sexparam"]+" -MAG_ZEROPOINT "+str(ZP)+ \
		" -DETECT_THRESH "+cfg["sigma"] + " -GAIN "+str(GAIN) +" -CHECKIMAGE_NAME "+self.aperturesfiles[i]
		print "EXECUTING:",sexStr
		res=commands.getoutput(sexStr)
		print res
		
		JDate=commands.getoutput("stilts calc \'isoToMjd(\"%s\")\'" % date)
		JDateCorrected=str(float(JDate)+float(self.exposure/(2*24*3600)))
		print date,JDate,JDateCorrected
		#DateCorrected=commands.getoutput("stilts calc \'mjdToIso(%s)\'" % JDateCorrected)
		#print date,JDate,JDateCorrected,DateCorrected
        	stiltsStr="stilts tpipe  cmd=\'addcol MJDATE \"%s\"\' \
        	     omode=out ofmt=fits-basic \
		     in=%s out=%s" % (JDateCorrected,filename,filename)
		#print stiltsStr
		res=commands.getoutput(stiltsStr)
		print res 
		self.setStats('date'+str(i),date)	
		self.setStats('sources'+str(i),self.recordsInCAT(filename))	

if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	sex=sextractor(fitsFiles)
	sex.do("SEXASTEROIDS")
