#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing
#Solve plates using Scamp Astromatic soft
#Alternative to eUsolveAstrometry.py
#Input:Fit(s) fits files to solve
#Output:S{InputFitsFiles}.fit
#config file parameters:
#
#	Section:[SOLVERSCAMP]
#		sexcfg
#		sexparam
#		sexfilter
#		scampcfg
#		swarpcfg
#Nacho Mas Junio 2013
#Status: work
import pyfits
import math
import commands,os, sys
import os.path
from eUconfig import *

cfg=dict(config.items("SOLVERSCAMP"))

class ScampSolver(helper):
	files_to_remove=""
	
	def do(self):

	  if not self.doAstrometry():
		return False

	  catslist=map(lambda x:os.path.join(os.path.dirname(x),""+os.path.basename(x)),self.catalogs)
	  cats=""
	  for c in catslist:
		cats=cats+" "+c

	  DEFAULT_ZP=float(cfg['default_zeropoint'])
	  for i,arg in enumerate(catslist):
		print ""	
        	print "FILE:",arg
		ZP=DEFAULT_ZP+2.5*math.log10(self.exposure)
		print "DEFAULT ZP:",DEFAULT_ZP, "ZERO POINT:",ZP
		sexStr="sex "+self.fits[i]+" -c "+cfg["sexcfg"]+" -CATALOG_NAME "+arg + \
		" -FILTER Y -FILTER_NAME "+cfg["sexfilter"] +" -PARAMETERS_NAME "+cfg["sexparam"] + " -MAG_ZEROPOINT "+str(ZP)
		print "EXECUTING:",sexStr
		res=commands.getoutput(sexStr)
		print res
		print "CATS:",cats
		if self.countSources(arg) <100:
			print "NOT ENOUGHT SOURCES FOR SOLVING. EXITING.."
			return False
			break

 	  #MIRROR SERVER -REF_SERVER vizier.nao.ac.jp
	  ucac4_server=cfg['ucac4_server']
	  ucac4_server=ucac4_server.replace('http://','')
	  cmd="scamp -REF_SERVER "+ucac4_server+" -ASTREF_CATALOG UCAC-4 -c "+cfg["scampcfg"] +" "+str(cats)
	  print cmd
	  res=commands.getoutput(cmd)
	  print res
	  if res.find("Not enough matched detections in instrument A1" )!=-1 \
		or res.find("Significant inaccuracy likely to occur in projection")!=-1 \
		or res.find("*Error*: No source found in reference catalog(s)")!=-1 :
		print "SCAMP FAIL!!!!!"
		return False
		 

	  for i,arg in  enumerate(self.solvefits):
		print "missfits "+arg
		res=commands.getoutput("missfits "+arg )
		print res
		res=commands.getoutput("mv "+arg+"s "+arg)
		print res
		
		if True:
			#CLEAN SIP HEADERS
	       		print "CLEANING SIP HEADERs IN:",arg
			#filename=os.path.splitext(arg)[0]
			hdulist = pyfits.open(arg,mode='update')
			#hdulist.info()
			header=hdulist[0].header
			DELheader=("A_ORDER","B_ORDER","AP_ORDER","BP_ORDER")
			for  key in DELheader:
				print "Deleting ",key
				del header[key]
			try:
				flxscale=float(header['FLXSCALE'])
				magzerop=float(header['MAGZEROP'])
			except:
				flxscale=0
				magzerop=0

			zeropoint=float(header['PHOT_C'])
			print flxscale,zeropoint
			if flxscale!=0:
				dmagzero=-2.5*math.log10(self.exposure*flxscale)-zeropoint+magzerop
			else:
				dmagzero=0
			
			#SOME FRAME IS BAD
			if abs(dmagzero)>4:
				dmagzero=0
				return False

			#TO be check
			#ZP=magzerop+dmagzero
			ZP=zeropoint+dmagzero
			header['DMAGZERO']=(dmagzero,"ZERO POINT FINE TUNE")
			header['ZMAG']=(ZP,"ZERO POINT")
			header['RADECSYS']=('FK5',"")
			header['EQUINOX']=(2000.0,"")
			header['CTYPE1']=('RA---TAN',"TAN GNOMIC + PV DISTORSION")
			header['CTYPE2']=('DEC--TAN',"TAN GNOMIC + PV DISTORSION")
			header['PIXSCALE']=(self.scale)
			header['ROTATION']=(self.rotation)
			hdulist.close()
	  #res=commands.getoutput("scamp -c "+cfg["scampcfg_phot"] +" UCAC-3_1542-1412_r169.cat "+str(cats))
	  #print res


	  self.clean()
	  print "SolverSAMP DONE:",arg
	  return True	

	def astrometry(self,img,parameters):
		cmd='solve-field  '+str(parameters)+" "+img
		print cmd
		res=commands.getoutput(cmd)
		print res
		field_rotation=res[res.find("Field rotation angle:"):].split('\n')[0][28:-16]
		#print field_rotation[28:-16]
		fits_info=res[res.find("Creating new FITS"):].split('\n')[0]
		#print "PPP"+fits_info[24:-4]+"PPP"
		try:
			self.rotation=float(field_rotation)
			self.scale=float(res[res.find('scale'):].split('\n')[0].split(' ')[1])
			self.newname=fits_info[24:-4]

		except:
			return False
		
		return 	True

	def countSources(self,cat):
		cmd="ldactoasc "+cat +"|sed  '/#/d'|wc -l"
		res=commands.getoutput(cmd)
		print "Count Sources:",int(res),"in cat:",cat
		return int(res)

	def doAstrometry(self):
		arg=self.fits[0]
		print ""	
        	print "FILE:",arg
		filename=os.path.splitext(arg)[0]
		print "Telescope:",self.telescope,self.telescopesN[0]
		params=cfg["astrometry_params"]
		print "solve-field params:",params
		if not self.astrometry(arg,params):
			print "Astrometry.net FAIL to solve"
			return False

		name=self.newname
		print "astrometry.net solved file:",name,self.solvefits[0]
		res=commands.getoutput("mv "+name.replace("new","wcs")+" .")
		print res


		wcs=os.path.basename(name.replace("new","wcs"))

		for i,f in enumerate(self.solvefits):
			res=commands.getoutput("cp "+wcs+" "+f.replace("fit","head"))
			print res
			res=commands.getoutput("missfits "+f )
			print res
			res=commands.getoutput("mv "+f+"s "+f)
			print res
			DEFAULT_ZP=float(cfg['default_zeropoint'])
	       		print "MAKE FRAME1 PHOTOMETRIC:",arg,DEFAULT_ZP
			hdulist = pyfits.open(f,mode='update')
			#hdulist.info()
			header=hdulist[0].header
			header['PHOT_C']=(DEFAULT_ZP,"")
			header['AIRMASS']=(1,"")
			header['PHOT_K']=(0,"")
			header['FILTER']=("V","")
			if i==0:
				header['PHOTFLAG']=(True,"")
			else:
				header['PHOTFLAG']=(False,"")
			hdulist.close()



		return True

			


	def clean(self):
		print "Cleanning"
 		res=commands.getoutput("rm "+self.files_to_remove)
		print res
	  	#Remove tmp files
		res=commands.getoutput("tmpreaper --verbose 1h /tmp" )
		print res
		"""
		try:		
	  		for filename in glob.glob('/tmp/tmp.sanitized.*') :
	    			os.remove( filename ) 
	  		for filename in glob.glob('/tmp/tmp.fit.*') :
	    			os.remove( filename ) 
	  		for filename in glob.glob('/tmp/tmp.ppm.*') :
	    			os.remove( filename ) 

		except:
			pass
		"""

if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	solver=ScampSolver(fitsFiles)
	solver.do()
