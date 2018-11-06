#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#Identify posible movers using rectal algoritms
#Input:source catalog of 3 consecutive frames 
#Output:same names but with 'Gcandidates_' file prefix
#config file parameters:
#
#	Section: [FCANDIDATES]
#		min_elongation
#		min_a_world
#		min_sep_loners1_2
#		max_sep_loners1_2
#		bolarectal
#		theta_theta_angle_diff
#		theta_rms_angle_diff
#
#Nacho Mas Junio 2013
#Status: work for La Sagra file

import pyfits
import shutil
import re
import numpy as np
import eUcatalog
import csv
import commands

from eUconfig import *

pi=np.pi

cfg=dict(config.items("FCANDIDATES"))
debug=cfg["debug"]
bolaRectal=float(cfg["bolarectal"])
angleDiff=float(cfg["theta_theta_angle_diff"])
RMSangleDiff=float(cfg["theta_rms_angle_diff"])
min_sep_loners1_2=float(cfg["min_sep_loners1_2"])
max_sep_loners1_2=float(cfg["max_sep_loners1_2"])


def Debug(string):
	if debug in ['True','true','yes','y']:
		print string


def Haversine((ra1,dec1),(ra2,dec2)):
	dra = ra2 - ra1
	ddec = dec2 - dec1
	a = sin(ddec/2)*sin(ddec/2) + cos(dec1) * cos(dec2) * sin(dra/2) * sin(dra/2)
	c = 2 * arcsin(min(1,sqrt(a)))
	return c

class candidates(helper):
	frameTime=[]
	files_to_remove="rectal1_2.cat rectal2_3.cat rectal_1_2_3.cat rectal_3_2_1.cat rectal_1_2_C.cat rectal_C_2_3.cat rectal_0_2_3.cat  rectal_1_2_0.cat  rectal_ALL.cat "
	def do(self):
		self.frameTime=[]
		for (i,cat) in enumerate(self.loners): 
			print i,cat
			self.frameTime.append(float(self.getMJDATEInCAT(cat))*24*3600)

		########SIN ACABAR!!!!
		"""
		#NUEVO ALGORITMO PARA SABER LAS SEPARACIONES
		### 
		t0=self.frameTime[0]
		t1=self.frameTime[1]
		t2=self.frameTime[2]
		print "FRAME MJDATES:",t0,t1,t2
		interframe_time1_2=t1-t0
		interframe_time2_3=t2-t1
		interframe_time1_3=t2-t0

		resolution=float(self.arcsecperpix)
		min_sep_1_3=(float(cfg["min_a_world"])*resolution/self.exposure)*interframe_time1_3
		max_sep_1_3=float(cfg["min_sep_pixel"])*resolution*2

		min_sep_triloners_1_2=(min_sep_loners1_2*interframe_time1_2/60)
		max_sep_triloners_1_2=(max_sep_loners1_2*interframe_time1_2/60)

		minspd=min_sep_1_3*60/interframe_time1_3
		maxspd=max_sep_1_3*60/interframe_time1_3
		print "ARCSECPERPIX:",resolution,"EXPTIME:",self.exposure,"InterFrame 1-3 time (s)",interframe_time1_3
		print "Min separation 1-3 (arcsec):",min_sep_1_3, " Max separation 1-3 (arcsec):",max_sep_1_3
		print "MIN SPD:",minspd,"MAX SPD:",maxspd
		"""

		#aplico el algoritmo rectal+ elipse a los triloner
		a_world=float(cfg["min_a_world"])
		MaxNtri=max(self.makeTriloners(a_world))

		#check for too much triloners. increase a_world until its reduce
		while MaxNtri >= float(cfg["max_triloners"]):
			print "TOO MUCH TRILONERS",MaxNtri,"/",float(cfg["max_triloners"])
			a_world=a_world*1.2
			print "INCRESING A_WORLD",a_world
			MaxNtri=max(self.makeTriloners(a_world))
			
		self.setStats('a_world',a_world)
		self.setStats('min_speed',a_world)
		#Check for trepidation
		if self.checkTrepidation():
			print "FRAME TREPIDATED!! EXITTING"
			return 0

		#primero en sentido directo
		self.do1_2()
		self.do1_2F()

		#luego en sentido inverso
		self.do2_3()
		self.do2_3F()

		#Junto todos las detecciones parciales
		stiltsStr="stilts tcat  ifmt=fits in=rectal_1_2_3.cat in=rectal_3_2_1.cat in=rectal_0_2_3.cat	\
				ocmd=\'delcols  ID' \
				ocmd=\'addcol  ID \"$0\"\'  \
			  in=rectal_1_2_0.cat ofmt=fits-basic out=rectal_ALL.cat"
		print stiltsStr
		res=commands.getoutput(stiltsStr)
		print res

		#Filtro las tablas de loner con los que han casado
		for (i,cat) in enumerate(self.triloners): 
			value1="NUMBER_"+str(i+1)
			framenumber=str(i+1)
			fitsfile=re.escape(self.solvefits[i])
			fitsfileCmd="addcol  FITSFILE \""+fitsfile+"\""
			stiltsStr="stilts tmatch2 find=best1 join=1and2 in1=rectal_ALL.cat	\
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
					DELTA_J2000 MJDATE MAG_AUTO MAGERR_AUTO FLAGS \
					FWHM X_IMAGE Y_IMAGE A_WORLD B_WORLD TRAIL_SPEED ELONGATION \
					THETA_J2000 PA0 PA0_ASTROMETRICA PA0_THETA PA0_THETA_SUR\"\'  \
				out=candidates_"+self.catalogs[i]+" ofmt=fits-basic "
			self.files_to_remove=self.files_to_remove+" candidates_"+self.catalogs[i]
			print stiltsStr
			res=commands.getoutput(stiltsStr)
			print res
		cat_with_records=[]
		for (i,cat) in enumerate(self.catalogs): 
			candi="candidates_"+cat
			if not os.path.isfile(candi):
				continue
			#candidates are limits to avoid computer overheads
			if self.recordsInCAT(candi)>0:
				cat_with_records.append(cat)
		
		
		if len(cat_with_records)==0:
			self.setStats('candidates',0)
			self.clean()
			return 0

		#Las uno y un poco de housekeeping
		stiltsStr="stilts tcatn nin="+str(len(cat_with_records))+" out="+self.Fcandidates+" ofmt=fits-basic  ocmd='sort ID' "
		for (i,cat) in enumerate(cat_with_records): 
			stiltsStr=stiltsStr+ " in"+str(i+1)+"=candidates_"+cat +" "
		res=commands.getoutput(stiltsStr)
		print res
		
		Ncandidates=self.recordsInCAT(self.Fcandidates)
		print "Creado:"+self.Fcandidates+" N:"+str(Ncandidates)
		self.setStats('candidates',Ncandidates)
		self.clean()
		return Ncandidates

	def clean(self):
		#return 0
 		res=commands.getoutput("rm "+self.files_to_remove)
		print res


	def makeTriloners(self,a_world):
		#selecciono las detecciones que tiene altas elongaciones 
		#y un tamaño (semiejemayor) apreciable
		#introduzco THETA_SUR para evitar discontinuidades en las comparaciones
		Ntri=[]
		for (i,cat) in enumerate(self.loners): 
			vector_x_c="addcol VECTOR_X (cos((90-THETA_J2000)*PI/180))"
		        vector_y_c="addcol VECTOR_Y (sin((90-THETA_J2000)*PI/180))"
			triloner_speed_cmd="addcol TRAIL_SPEED ("+str(np.sqrt(3))+"*2*A_WORLD*3600*60/"+str(self.exposure)+")"
	        	theta_sur_c="addcol THETA_SUR ((THETA_J2000>=0)?(180-THETA_J2000):(-THETA_J2000))"
			min_elongation_cmd="select \"ELONGATION>="+cfg["min_elongation"]+"\""
			min_a_world_cmd="select \"A_WORLD*3600>="+str(a_world)+"\""
			stiltsStr="stilts tpipe in="+cat +"	\
				cmd=\'"+min_elongation_cmd+ "\' \
				cmd=\'"+min_a_world_cmd+ "\' \
				cmd=\'"+triloner_speed_cmd+ "\' \
	 		        out="+self.triloners[i] +" ofmt=fits-basic  \
				cmd=\'addcol  FRAME \""+str(i+1)+"\"\'  \
				cmd=\'"+theta_sur_c+ "\' \
				"
			Debug(stiltsStr)
			print "Creando triloners"
			res=commands.getoutput(stiltsStr)
			Debug(res)
			ntriloners=self.recordsInCAT(self.triloners[i])
			Ntri.append(ntriloners)
			self.setStats('triloners'+str(i),ntriloners)
		return Ntri

	#CHECK FOR TREPIDATION
	#SOME FRAMES HAS A LOT OF ELLIPSE BECAUSE THERE ARE MOVED
	#IF IT IS THE CASE MORE OF THE ELLIPSE HAVE THE SAME THETA_J2000 
	def checkTrepidation(self):
		for (i,cat) in enumerate(self.triloners): 
			stiltsStr="stilts tmatch1 in="+cat +"	\
				matcher=1d params=0.01 action=identify \
				values='THETA_J2000' \
				icmd='keepcols \"THETA_J2000\"' \
				ocmd='keepcols \"groupSize\"' \
				omode=stats \
				"

			res=commands.getoutput(stiltsStr)
			try:
				lines=res.split('\n')
				results=lines[-2].split('|')
				maxEllipses=int(results[5])
			except:
				maxEllipses=0
			print "Check for Trepidated frames",self.solvefits[i]," :",maxEllipses
			self.setStats('trepidation'+str(i),maxEllipses)
			if maxEllipses>int(cfg['trepidate']):
				print "Frame ",self.solvefits[i], " is trepidated. Exiting"
				self.setStats('trepidated',True)
				return True
		self.setStats('trepidated',False)
		return False
	
	def do1_2(self):		
		t0=self.frameTime[0]
		t1=self.frameTime[1]
		t2=self.frameTime[2]
		#Miro los loners del frame 2 que estan cerca en el frame 1
		#y que tienen THETAS pareceidos. Se compara tanto THETA_J2000 como THETA_SUR 
		# 
		interframe_time1_2=t1-t0
		min_sep_triloners_1_2=(min_sep_loners1_2*interframe_time1_2/60)
		max_sep_triloners_1_2=(max_sep_loners1_2*interframe_time1_2/60)
		print "EXPTIME:",self.exposure,"InterFrame time",interframe_time1_2
		print "Min separation:",min_sep_triloners_1_2, " Max separation:",max_sep_triloners_1_2


		min_sep_cmd="select \"Separation>="+str(min_sep_triloners_1_2)+"\""
		similar_thetas_cmd="select \"(abs(THETA_J2000_1-THETA_J2000_2)<"+str(angleDiff)+"||abs(THETA_SUR_1-THETA_SUR_2)<"+str(angleDiff)+")\""
		stiltsStr="stilts tmatch2 find=all join=1and2 in1="+self.triloners[0] +"	\
			in2="+self.triloners[1] +"	\
			values1=\"ALPHA_J2000 DELTA_J2000\" \
			values2=\"ALPHA_J2000 DELTA_J2000\" \
			fixcols=all suffix1='_1' suffix2='_2' matcher=sky params="+str(max_sep_triloners_1_2) +"  \
	 	        out=rectal1_2.cat ofmt=fits-basic  \
			ocmd=\'"+ similar_thetas_cmd+"\' \
			ocmd=\'"+min_sep_cmd+"\' \
			"
		print   stiltsStr
		print "Creando rectal 1-2"
		res=commands.getoutput(stiltsStr)
		print res

		#1-2Calculo posicion teorica si es un fast mover
		#de paso filtro los que tiene un PA_THETA similiar a THETA_J2000

		T=(t2-t0)/(t1-t0)
		print T
		delta_c="addcol DELTA_J2000_C (DELTA_J2000_1+(DELTA_J2000_2-DELTA_J2000_1)*"+str(T)+")"
		#alpha_c="addcol ALPHA_J2000_C ((ALPHA_J2000_1*cos(degreesToRadians(DELTA_J2000_1))+(ALPHA_J2000_2*cos(degreesToRadians(DELTA_J2000_2))-ALPHA_J2000_1*cos(degreesToRadians(DELTA_J2000_2)))*"+str(T)+")/cos(degreesToRadians(DELTA_J2000_C)))"
		alpha_c="addcol ALPHA_J2000_C (ALPHA_J2000_1+(ALPHA_J2000_2-ALPHA_J2000_1)*"+str(T)+")"
		#pa_c="addcol PA0 ((180/PI)*atan2((DELTA_J2000_2-DELTA_J2000_1),(ALPHA_J2000_2*cos(degreesToRadians(DELTA_J2000_2))-ALPHA_J2000_1*cos(degreesToRadians(DELTA_J2000_2)))))"

		#Está mal. Falla para 0>PA>90
		#pa_c="addcol PA0 ((180/PI)*atan2((DELTA_J2000_2-DELTA_J2000_1),(ALPHA_J2000_2-ALPHA_J2000_1)))"	
		#pa_theta_c="addcol PA0_THETA (PA0>180?(270-PA0):PA0<0?(-90-PA0):(90-PA0))" 

		pa_c="addcol PA0 ((180/PI)*atan2((ALPHA_J2000_2-ALPHA_J2000_1)*cos(degreesToRadians(DELTA_J2000_2)),(DELTA_J2000_2-DELTA_J2000_1)))"
		#pa_c="addcol PA0 ((180/PI)*atan2((ALPHA_J2000_2-ALPHA_J2000_1),(DELTA_J2000_2-DELTA_J2000_1)))"		


		pa_astrometrica_c="addcol PA0_ASTROMETRICA (PA0>=0?PA0:(360+PA0))"  
		pa_theta_c="addcol PA0_THETA (PA0_ASTROMETRICA<90?PA0_ASTROMETRICA:PA0_ASTROMETRICA<270?(PA0_ASTROMETRICA-180):(PA0_ASTROMETRICA-360))" 

		pa_theta_sur_c="addcol PA0_THETA_SUR ((PA0_THETA>=0)?(180-PA0_THETA):(-PA0_THETA))"
		similar_thetas_cmd="select \"(abs(THETA_J2000_1-PA0_THETA)<"+str(RMSangleDiff)+"||abs(THETA_SUR_1-PA0_THETA_SUR)<"+str(RMSangleDiff)+")\""
		MAX_SEP_0=np.tan(bolaRectal*pi/180)
		MAX_SEP="addcol MAX_SEP (Separation*"+str(MAX_SEP_0)+")"
		mocfile="moc_"+re.escape(self.fits[2])
		out_frame_c="addcol C_OUT_FLAG (inMoc(\""+mocfile+"\",ALPHA_J2000_C,DELTA_J2000_C))"
		#MAX_SEP="addcol MAX_SEP (10*"+str(MAX_SEP_0)+")"
		stiltsStr="stilts tpipe in=rectal1_2.cat \
		  cmd=\'"+delta_c+ "\' \
		  cmd=\'"+alpha_c+ "\' \
		  cmd=\'"+pa_c+ "\' \
		  cmd=\'"+MAX_SEP+ "\' \
		  cmd=\'"+pa_astrometrica_c+ "\' \
		  cmd=\'"+pa_theta_c+ "\' \
		  cmd=\'"+pa_theta_sur_c+ "\' \
		  cmd=\'"+similar_thetas_cmd+ "\' \
		  out=rectal_1_2_C.cat ofmt=fits-basic"



		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res


		#1-2Comparo con los loners del frame3. 
		similar_thetas_cmd="select \"(abs(PA0_THETA-THETA_J2000_3)<"+str(RMSangleDiff)+"||abs(PA0_THETA_SUR-THETA_SUR_3)<"+str(RMSangleDiff)+")\""
		stiltsStr="stilts tmatch2 find=all join=1and2 in1=rectal_1_2_C.cat	\
			in2="+self.triloners[2] +"	\
			matcher=skyerr params=1  \
			values1=\"ALPHA_J2000_C DELTA_J2000_C MAX_SEP\" \
			values2=\"ALPHA_J2000 DELTA_J2000 0\" \
			suffix1='' suffix2='_3' \
			fixcols=all \
	  	        ocmd='addcol ID \"index\"' \
	  	        ocmd='sort ID' \
			ocmd=\'"+ similar_thetas_cmd+"\' \
			ocmd='keepcols \"ID NUMBER_1 NUMBER_2 NUMBER_3 PA0 PA0_ASTROMETRICA  PA0_THETA PA0_THETA_SUR\"' \
	  	        out=rectal_1_2_3.cat ofmt=fits-basic"

		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res

	def do2_3(self):
		t0=self.frameTime[0]
		t1=self.frameTime[1]
		t2=self.frameTime[2]

		#Ahora lo mismo pero comparando frames 2-3
		#Miro los loners del frame 2 que estan cerca en el frame 1
		#y que tienen THETAS pareceidos. Se compara tanto THETA_J2000 como THETA_SUR 
		# 
		interframe_time2_3=t2-t1
		min_sep_triloners_2_3=(min_sep_loners1_2*interframe_time2_3/60)
		max_sep_triloners_2_3=(max_sep_loners1_2*interframe_time2_3/60)
		print "EXPTIME:",self.exposure,"InterFrame time",interframe_time2_3
		print "Min separation:",min_sep_triloners_2_3, " Max separation:",max_sep_triloners_2_3

		min_sep_cmd="select \"Separation>="+str(min_sep_triloners_2_3)+"\""
		similar_thetas_cmd="select \"(abs(THETA_J2000_2-THETA_J2000_3)<"+str(angleDiff)+"||abs(THETA_SUR_2-THETA_SUR_3)<"+str(angleDiff)+")\""
		stiltsStr="stilts tmatch2 find=all join=1and2 in1="+self.triloners[1] +"	\
			in2="+self.triloners[2] +"	\
			values1=\"ALPHA_J2000 DELTA_J2000\" \
			values2=\"ALPHA_J2000 DELTA_J2000\" \
			fixcols=all suffix1='_2' suffix2='_3' matcher=sky params="+str(max_sep_triloners_2_3) +"  \
	 	        out=rectal2_3.cat ofmt=fits-basic  \
			ocmd=\'"+ similar_thetas_cmd+"\' \
			ocmd=\'"+min_sep_cmd+"\' \
			"
		print   stiltsStr
		print "Creando rectal 2-3"
		res=commands.getoutput(stiltsStr)
		print res

		#2-3 Calculo posicion teorica si es un fast mover
		#de paso filtro los que tiene un PA_THETA similiar a THETA_J2000
		T=(t0-t1)/(t2-t1)
		print T
		delta_c="addcol DELTA_J2000_C (DELTA_J2000_2+(DELTA_J2000_3-DELTA_J2000_2)*"+str(T)+")"
		#alpha_c="addcol ALPHA_J2000_C ((ALPHA_J2000_2*cos(degreesToRadians(DELTA_J2000_2))+(ALPHA_J2000_3*cos(degreesToRadians(DELTA_J2000_3))-ALPHA_J2000_2*cos(degreesToRadians(DELTA_J2000_3)))*"+str(T)+")/cos(degreesToRadians(DELTA_J2000_C)))"
		alpha_c="addcol ALPHA_J2000_C (ALPHA_J2000_2+(ALPHA_J2000_3-ALPHA_J2000_2)*"+str(T)+")"
		#pa_c="addcol PA0 ((180/PI)*atan2((DELTA_J2000_3-DELTA_J2000_2),(ALPHA_J2000_3*cos(degreesToRadians(DELTA_J2000_3))-ALPHA_J2000_2*cos(degreesToRadians(DELTA_J2000_3)))))"

		#Está mal. Falla para 0>PA>90
		#pa_c="addcol PA0 ((180/PI)*atan2((DELTA_J2000_3-DELTA_J2000_2),(ALPHA_J2000_3-ALPHA_J2000_2)))"	
		#pa_theta_c="addcol PA0_THETA (PA0>180?(270-PA0):PA0<0?(-90-PA0):(90-PA0))"

		pa_c="addcol PA0 ((180/PI)*atan2((ALPHA_J2000_3-ALPHA_J2000_2)*cos(degreesToRadians(DELTA_J2000_2)),(DELTA_J2000_3-DELTA_J2000_2)))"
		#pa_c="addcol PA0 ((180/PI)*atan2((ALPHA_J2000_3-ALPHA_J2000_2),(DELTA_J2000_3-DELTA_J2000_2)))"
	
		pa_astrometrica_c="addcol PA0_ASTROMETRICA (PA0>=0?PA0:(360+PA0))"  
		pa_theta_c="addcol PA0_THETA (PA0_ASTROMETRICA<90?PA0_ASTROMETRICA:PA0_ASTROMETRICA<270?(PA0_ASTROMETRICA-180):(PA0_ASTROMETRICA-360))" 

		pa_theta_sur_c="addcol PA0_THETA_SUR ((PA0_THETA>=0)?(180-PA0_THETA):(-PA0_THETA))"
		similar_thetas_cmd="select \"(abs(THETA_J2000_2-PA0_THETA)<"+str(RMSangleDiff)+"||abs(THETA_SUR_2-PA0_THETA_SUR)<"+str(RMSangleDiff)+")\""
		MAX_SEP_0=np.tan(bolaRectal*pi/180)
		MAX_SEP="addcol MAX_SEP (Separation*"+str(MAX_SEP_0)+")"
		stiltsStr="stilts tpipe in=rectal2_3.cat \
		  cmd=\'"+delta_c+ "\' \
		  cmd=\'"+alpha_c+ "\' \
		  cmd=\'"+pa_c+ "\' \
		  cmd=\'"+MAX_SEP+ "\' \
		  cmd=\'"+pa_astrometrica_c+ "\' \
		  cmd=\'"+pa_theta_c+ "\' \
		  cmd=\'"+pa_theta_sur_c+ "\' \
		  cmd=\'"+similar_thetas_cmd+ "\' \
		  out=rectal_C_2_3.cat ofmt=fits-basic"


		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res

		#2-3Comparo con los loners del frame1. 
		similar_thetas_cmd="select \"(abs(PA0_THETA-THETA_J2000_1)<"+str(RMSangleDiff)+"||abs(PA0_THETA_SUR-THETA_SUR_1)<"+str(RMSangleDiff)+")\""
		stiltsStr="stilts tmatch2 find=all join=1and2 in1=rectal_C_2_3.cat	\
			in2="+self.triloners[0] +"	\
			matcher=skyerr params=1  \
			values1=\"ALPHA_J2000_C DELTA_J2000_C MAX_SEP\" \
			values2=\"ALPHA_J2000 DELTA_J2000 0\" \
			suffix1='' suffix2='_1' \
			fixcols=all \
	  	        ocmd='addcol ID \"index\"' \
	  	        ocmd='sort ID' \
			ocmd=\'"+ similar_thetas_cmd+"\' \
			ocmd='keepcols \"ID NUMBER_1 NUMBER_2 NUMBER_3 PA0 PA0_ASTROMETRICA PA0_THETA PA0_THETA_SUR\"' \
	  	        out=rectal_3_2_1.cat ofmt=fits-basic"

		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res


	def do1_2F(self):
		#1-2Miro si es tan rapido que se sale
		print "SEARCHING VERY-FAST-MOVERS VERY-FAST-MOVERS VERY-FAST-MOVERS"
		print "SEARCHING VERY-FAST-MOVERS VERY-FAST-MOVERS VERY-FAST-MOVERS"

		maxA=cfg['theta_theta_angle_diff_extra']
		minT=cfg['min_a_world_extra']
		minE=cfg['min_elongation_extra']
		ThetaRMSangleDiff=cfg['theta_rms_angle_diff_extra']
		similar_thetas_cmd="select \"(abs(THETA_J2000_1-THETA_J2000_2)<"+str(maxA)+"|| abs(THETA_SUR_1-THETA_SUR_2)<"+str(maxA)+")\""
		min_trailsize_cmd="select \"(A_WORLD_1*3600>"+str(minT)+" && A_WORLD_2*3600>"+str(minT)+")\""
		min_elongation_cmd="select \"(ELONGATION_1>"+str(minE)+" && ELONGATION_2>"+str(minE)+")\""
		similar_rmsthetas1_cmd="select \"(abs(THETA_J2000_1-PA0_THETA)<"+str(ThetaRMSangleDiff)+"||abs(THETA_SUR_1-PA0_THETA_SUR)<"+str(ThetaRMSangleDiff)+")\""
		similar_rmsthetas2_cmd="select \"(abs(THETA_J2000_2-PA0_THETA)<"+str(ThetaRMSangleDiff)+"||abs(THETA_SUR_2-PA0_THETA_SUR)<"+str(ThetaRMSangleDiff)+")\""
		stiltsStr="stilts tpipe in=rectal_1_2_C.cat	\
	  	        cmd='addcol ID \"index\"' \
	  	        cmd='sort ID' \
	  	        cmd='addcol NUMBER_3 \"toInteger(0)\"' \
			cmd=\'"+ min_trailsize_cmd+"\' \
			cmd=\'"+ similar_thetas_cmd+"\' \
			cmd=\'"+ similar_rmsthetas1_cmd+"\' \
			cmd=\'"+ similar_rmsthetas2_cmd+"\' \
			cmd=\'"+ min_elongation_cmd+"\' \
			cmd='keepcols \"ID NUMBER_1 NUMBER_2 NUMBER_3 PA0 PA0_ASTROMETRICA PA0_THETA PA0_THETA_SUR\"' \
	  	        out=rectal_1_2_0.cat ofmt=fits-basic"

		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res

	def do2_3F(self):
		#2-3Miro si es tan rapido que se sale
		print "SEARCHING VERY-FAST-MOVERS VERY-FAST-MOVERS VERY-FAST-MOVERS"
		print "SEARCHING VERY-FAST-MOVERS VERY-FAST-MOVERS VERY-FAST-MOVERS"
		maxA=cfg['theta_theta_angle_diff_extra']
		minT=cfg['min_a_world_extra']
		minE=cfg['min_elongation_extra']
		ThetaRMSangleDiff=cfg['theta_rms_angle_diff_extra']
		similar_thetas_cmd="select \"(abs(THETA_J2000_2-THETA_J2000_3)<"+str(maxA)+" || abs(THETA_SUR_2-THETA_SUR_3)<"+str(maxA)+")\""
		min_trailsize_cmd="select \"(A_WORLD_2*3600>"+str(minT)+" && A_WORLD_3*3600>"+str(minT)+")\""
		min_elongation_cmd="select \"(ELONGATION_2>"+str(minE)+" && ELONGATION_3>"+str(minE)+")\""
		similar_rmsthetas1_cmd="select \"(abs(THETA_J2000_3-PA0_THETA)<"+str(ThetaRMSangleDiff)+"||abs(THETA_SUR_3-PA0_THETA_SUR)<"+str(ThetaRMSangleDiff)+")\""
		similar_rmsthetas2_cmd="select \"(abs(THETA_J2000_2-PA0_THETA)<"+str(ThetaRMSangleDiff)+"||abs(THETA_SUR_2-PA0_THETA_SUR)<"+str(ThetaRMSangleDiff)+")\""
		stiltsStr="stilts tpipe in=rectal_C_2_3.cat	\
	  	        cmd='addcol ID \"index\"' \
	  	        cmd='sort ID' \
	  	        cmd='addcol NUMBER_1 \"toInteger(0)\"' \
			cmd=\'"+ min_trailsize_cmd+"\' \
			cmd=\'"+ similar_thetas_cmd+"\' \
			cmd=\'"+ similar_rmsthetas1_cmd+"\' \
			cmd=\'"+ similar_rmsthetas2_cmd+"\' \
			cmd=\'"+ min_elongation_cmd+"\' \
			cmd='keepcols \"ID NUMBER_1 NUMBER_2 NUMBER_3 PA0 PA0_ASTROMETRICA PA0_THETA PA0_THETA_SUR\"' \
	  	        out=rectal_0_2_3.cat ofmt=fits-basic"

		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res



if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	c=candidates(fitsFiles)
	#c.checkTrepidation()
	c.do()


