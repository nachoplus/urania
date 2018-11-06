#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#Identify posible movers using rectal algoritms
#Input:source catalog of 3 consecutive frames 
#Output:same names but with 'Gcandidates_' file prefix
#config file parameters:
#
#	Section: [ACANDIDATES]
#		min_sep_loners1_3
#		max_sep_loners1_3
#		bolaRectal
#
#Nacho Mas Junio 2013
#Status: work for La Sagra file


import pyfits
from pylab import *
import shutil
import re
import numpy as np
import math
import commands

from eUconfig import *
cfg=dict(config.items("ACANDIDATES"))


class candidates(helper):
	files_to_remove="rectal.cat rectal0.cat "
	def do(self):
		#alphaLoner3=math.tan(float(cfg["bolarectal"])*pi/180)
		alphaLoner3=float(cfg["bolarectal"])
		betweenPercent=float(cfg["betweenpercent"])
		print "alphaLoner3:",alphaLoner3,"betweenPercent:",betweenPercent
		self.frameTime=[]
		for (i,cat) in enumerate(self.loners): 
			mjd=self.getMJDATEInCAT(cat)
			print "MJD:",i,mjd
			self.frameTime.append(float(mjd)*24*3600)

		t0=self.frameTime[0]
		t1=self.frameTime[1]
		t2=self.frameTime[2]
		print "FRAME MJDATES:",t0,t1,t2
		interframe_time1_3=t2-t0
		"""	
		min_sep_loners1_3=float(cfg["min_sep_loners1_3"])
		max_sep_loners1_3=float(cfg["max_sep_loners1_3"])

		min_sep_1_3=(min_sep_loners1_3*interframe_time1_3/60)
		max_sep_1_3=(max_sep_loners1_3*interframe_time1_3/60)
		"""
		#NUEVO ALGORITMO PARA SABER LAS SEPARACIONES
		#La minima directa en pixeles en el cfg
		resolution=float(self.arcsecperpix)
		min_sep_1_3=float(cfg["min_sep_pixel"])*resolution*2
		max_trail_legth=np.sqrt(3)*2*float(cfg['max_a_world'])
		#max_sep_1_3=(float(cfg["max_trail_legth"])*resolution/self.exposure)*interframe_time1_3
		max_sep_1_3=(max_trail_legth/self.exposure)*interframe_time1_3

		minspd=min_sep_1_3*60/interframe_time1_3
		maxspd=max_sep_1_3*60/interframe_time1_3
		print "ARCSECPERPIX:",resolution,"EXPTIME:",self.exposure,"InterFrame 1-3 time (s)",interframe_time1_3
		print "Min separation 1-3 (arcsec):",min_sep_1_3, " Max separation 1-3 (arcsec):",max_sep_1_3
		print "MIN SPD:",minspd,"MAX SPD:",maxspd

		#Miro los loners del frame 3 que estan cerca en el frame 1
		min_sep_cmd="select \"Separation>="+str(min_sep_1_3)+"\""
		stiltsStr="stilts tmatch2 find=all join=1and2 in1="+self.loners[0] +"	\
		in2="+self.loners[2] +"	\
		values1=\"ALPHA_J2000 DELTA_J2000\" \
		values2=\"ALPHA_J2000 DELTA_J2000\" \
		fixcols=all suffix1='_1' suffix2='_3' matcher=sky params="+str(max_sep_1_3) +"  \
 	        out=rectal.cat ofmt=fits-basic  \
		ocmd=\'"+min_sep_cmd+"\' \
		"

		print   stiltsStr
		print "Creando rectal"
		res=commands.getoutput(stiltsStr)
		print res


		#Leo datetime 
		"""
		stiltsStr="stilts tpipe cmd=\'head 1\' in="+self.loners[0]  +"	\
		   cmd='keepcols \"MJDATE\"' \
             	   omode=out ofmt=csv-noheader"
		t0=float(commands.getoutput(stiltsStr))

		stiltsStr="stilts tpipe cmd=\'head 1\' in="+self.loners[1] +"	\
		   cmd='keepcols \"MJDATE\"' \
             	   omode=out ofmt=csv-noheader"
		t1=float(commands.getoutput(stiltsStr))

		stiltsStr="stilts tpipe cmd=\'head 1\' in="+self.loners[2] +"	\
		   cmd='keepcols \"MJDATE\"' \
             	   omode=out ofmt=csv-noheader"
		t2=float(commands.getoutput(stiltsStr))
		"""
		FLIGTH_TIME0=(double(t1)-double(t0))*24*3600
		FLIGTH_TIME1=(double(t2)-double(t1))*24*3600
		print t0,t1,t2,FLIGTH_TIME0,FLIGTH_TIME1

		#Calculo posicion teorica si es un mover
		T=(t1-t0)/(t2-t0)
		print T
		delta_c="addcol DELTA_J2000_C (DELTA_J2000_1+(DELTA_J2000_3-DELTA_J2000_1)*"+str(T)+")"
		alpha_c="addcol ALPHA_J2000_C ((ALPHA_J2000_1*cos(degreesToRadians(DELTA_J2000_1))+(ALPHA_J2000_3*cos(degreesToRadians(DELTA_J2000_3))-ALPHA_J2000_1*cos(degreesToRadians(DELTA_J2000_1)))*"+str(T)+")/cos(degreesToRadians(DELTA_J2000_C)))"

		#MAX_SEP="addcol MAX_SEP (maxReal(2,Separation*"+str(alphaLoner3)+"))"
		MAX_SEP="addcol MAX_SEP (minReal("+str(alphaLoner3)+",Separation*"+str(betweenPercent)+"))"
		#MAX_SEP="addcol MAX_SEP (Separation*"+str(alphaLoner3)+")"
		stiltsStr="stilts tpipe in=rectal.cat \
		  cmd=\'"+delta_c+ "\' \
		  cmd=\'"+alpha_c+ "\' \
		  cmd=\'"+MAX_SEP+ "\' \
		  out=rectal0.cat ofmt=fits-basic"

		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res


		#Comparo con los loners del frame2. 
		stiltsStr="stilts tmatch2 find=best join=1and2 in1=rectal0.cat	\
			in2="+self.loners[1] +"	\
			matcher=skyerr params=1  \
			values1=\"ALPHA_J2000_C DELTA_J2000_C MAX_SEP\" \
			values2=\"ALPHA_J2000 DELTA_J2000 0\" \
			suffix1='' suffix2='_2' \
			fixcols=all \
	  	        ocmd='addcol ID \"index\"' \
	  	        ocmd='sort ID' \
			ocmd='keepcols \"ID NUMBER_1 NUMBER_2 NUMBER_3\"' \
	  	        out=rectal.cat ofmt=fits-basic"


		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res

		#Filtro las tablas de loner con los que han casado
		for (i,cat) in enumerate(self.loners): 
			value1="NUMBER_"+str(i+1)
			framenumber=str(i+1)
			fitsfile=re.escape(self.solvefits[i])
			fitsfileCmd="addcol  FITSFILE \""+fitsfile+"\""
			stiltsStr="stilts tmatch2 find=best1 join=1and2 in1=rectal.cat	\
				in2="+cat +"	\
				matcher=exact  \
				values1=\""+value1+"\" \
				values2=\"NUMBER\" \
				ocmd=\'addcol  FRAME \""+framenumber+"\"\'  \
				ocmd=\'addcol  DATETIME \"(mjdToIso(MJDATE))\"\'  \
				ocmd=\'addcol  RA \"(degreesToHms( ALPHA_J2000, 2 ))\"\'  \
				ocmd=\'addcol  DEC \"(degreesToDms( DELTA_J2000, 2 ))\"\'  \
				ocmd=\'addcol  FWHM \"(FWHM_WORLD*3600)\"\'  \
				ocmd=\'keepcols \"ID FRAME  DATETIME RA DEC ALPHA_J2000 \
				DELTA_J2000 MJDATE MAG_AUTO MAGERR_AUTO FLAGS FWHM X_IMAGE Y_IMAGE \"\'  \
				out=candidates_"+self.catalogs[i]+" ofmt=fits-basic "
			self.files_to_remove=self.files_to_remove+" candidates_"+self.catalogs[i]
			print stiltsStr
			res=commands.getoutput(stiltsStr)
			print res



		#Las uno y un poco de housekeeping
		cat_with_records=[]
		for (i,cat) in enumerate(self.catalogs): 
			candi="candidates_"+cat
			if not os.path.isfile(candi):
				continue
			#candidates are limits to avoid computer overheads
			if self.recordsInCAT(candi)>0 and self.recordsInCAT(candi)<int(cfg['max_candidates']):
				cat_with_records.append(cat)
		
		
		if len(cat_with_records)!=3:
			self.setStats('candidates',0)
			self.clean()
			return 0


		stiltsStr="stilts tcatn nin="+str(len(cat_with_records))+" out="+self.Acandidates+" ofmt=fits-basic  ocmd='sort ID' "
		for (i,cat) in enumerate(self.catalogs): 
			stiltsStr=stiltsStr+ " in"+str(i+1)+"=candidates_"+cat +" "
		res=commands.getoutput(stiltsStr)
		print res

		Ncandidates=self.recordsInCAT(self.Acandidates)
		print "Creado:"+self.Acandidates+" N:"+str(Ncandidates)
		self.setStats('candidates',Ncandidates)
		self.clean()
		return Ncandidates



	def clean(self):
 		res=commands.getoutput("rm "+self.files_to_remove)
		print res
		

if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	c=candidates(fitsFiles)
	c.do()
