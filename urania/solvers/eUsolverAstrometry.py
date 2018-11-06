#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing
#Solve plates using astrometry.net soft
#Alternative to eUsolveScamp.py
#Input:Fit(s) fits files to solve
#Output:S{InputFitsFiles}.fit
#config file parameters:
#
#	Section:[SOLVERASTROMETRY]
#		params
#Nacho Mas Junio 2013
#Status: work
import pyfits

import commands,os, sys,glob
from eUconfig import *
cfg=dict(config.items("SOLVERASTROMETRY"))

class AstrometryNetSolver(helper):

	def astrometry(self,img,parameters):
		cmd='solve-field  '+str(parameters)+" "+img
		print cmd
		res=commands.getoutput(cmd)
		#print res
		field_rotation=res[res.find("Field rotation angle:"):].split('\n')[0]
		#print field_rotation[28:-16]
		fits_info=res[res.find("Creating new FITS"):].split('\n')[0]
		#print "PPP"+fits_info[24:-4]+"PPP"
		return 	(fits_info[24:-4],field_rotation[28:-16])



	def do(self):
	  cats=""
	  for i,arg in enumerate(self.fits):
		print ""	
        	print "FILE:",arg
		filename=os.path.splitext(arg)[0]
		scale_guess=cfg["scale_guess"].split(',')
		print "Telescope:",self.telescope,self.telescopesN[0]
		params=cfg["params"]+" "+scale_guess[self.telescopesN[0]]
		print "solve-field params:",params
		name,field_rotation=self.astrometry(arg,params)
		print name,field_rotation
		try:
			rotation=float(field_rotation)
		except:
			return False
		self.update_hdr(name,'ROTATION',rotation)
		self.update_hdr(name,'RADECSYS','FK5')
		self.update_hdr(name,'EQUINOX',2000.0)
		self.update_hdr(name,'EPOCH',2000.0)
		print "solved file:",name,self.solvefits[i]
		res=commands.getoutput("mv "+name+" "+self.solvefits[i])

		print res
	  #Remove tmp files
	  try:		
	  	for filename in glob.glob('/tmp/tmp.sanitized.*') :
	    		os.remove( filename ) 
	  	for filename in glob.glob('/tmp/tmp.fit.*') :
	    		os.remove( filename ) 
	  	for filename in glob.glob('/tmp/tmp.ppm.*') :
	    		os.remove( filename ) 

	  except:
		pass	
	  return True



if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	solver=AstrometryNetSolver(fitsFiles)
	solver.do()
