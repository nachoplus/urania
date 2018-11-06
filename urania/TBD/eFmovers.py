#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import pyfits
import commands,os, sys
import shutil
import csv
import re
import numpy as np
import eUcatalog


from eUconfig import *
cfg=dict(config.items("FMOVERS"))
debug=cfg["debug"]

pi=np.pi

def Haversine((ra1,dec1),(ra2,dec2)):
	dra = ra2 - ra1
	ddec = dec2 - dec1
	a = np.sin(ddec/2)*np.sin(ddec/2) + np.cos(dec1) * np.cos(dec2) * np.sin(dra/2) * np.sin(dra/2)
	c = 2 * np.arcsin(min(1,np.sqrt(a)))
	return c

class checkMovers(eUcatalog.moverCat,helper):
	addHeader=(["speed","MEAN_MAG","MEANSpeed","stdSpeed","TRAILNESS","W[0]","W[1]", \
		"PA","PA_ASTROMETRICA","LINE_DIS","CORRELATION","GOODFLAG","DESIGNATION"])
	rows=[]
	files_to_remove=" "
	#distancia de un punto (ra,dec) a una recta de coeficientes w (a=w[0],b=w[1])
	def dis(self,ra,dec,w):
		return (w[0]*ra-dec+w[1])/(w[0]*w[0]+1)

	def do(self):
 	 self.rows=[]
	 self.pearlindex={}
 	 self.loadFIT(self.Fcandidates)
	 movers=self.data
	 moversIDs=set(movers['ID'])
	 #print  moversIDs	
	 for j,moverID in enumerate(moversIDs):
		moverFlt=(movers['ID']==moverID)
		mover=movers[moverFlt]

		#DOUBLE CHECK
		if len(mover)<2:
			continue

		mag_auto=map(lambda x:float(x['MAG_AUTO']),mover)
		meanmag_auto=np.mean(mag_auto)
		stdmag_auto=np.std(mag_auto)


		###Ajuste de una recta por minimos cuadrados
		######MEJOR EN PIIXEL!!!!!
		#RAs=map(lambda x:float(x['ALPHA_J2000']*cos(x['DELTA_J2000']*np.pi/180)),mover)
		RAs=map(lambda x:float(x['ALPHA_J2000']),mover)
		x=np.array([RAs,np.ones(len(RAs))]).T

		DECs=map(lambda x:float(x['DELTA_J2000']),mover)
		y=DECs
		lst = np.linalg.lstsq(x,y)
		w=lst[0]
		THETAs=map(lambda x:float(x['THETA_J2000']),mover)
		MeanTheta=np.mean(THETAs)

		TRAILs=map(lambda x:float(np.sqrt(3)*2*x['A_WORLD']*3600),mover)
		

		TIMEs=map(lambda x:float(x['MJDATE'])*3600*24,mover)
		#print TIMEs

		X_IMAGEs=map(lambda x:float(x['X_IMAGE']),mover)
		xImageMean=np.mean(X_IMAGEs)
		xImageStd=np.std(X_IMAGEs)
		xImageMax=np.max(map(lambda x:x-xImageMean,X_IMAGEs))
		#print moverID,"XXXXX",xImageMax,xImageMean
		#print X_IMAGEs


		Y_IMAGEs=map(lambda x:float(x['Y_IMAGE']),mover)
		yImageMean=np.mean(Y_IMAGEs)
		yImageStd=np.std(Y_IMAGEs)
		yImageMax=np.max(map(lambda x:x-yImageMean,Y_IMAGEs))
		#print moverID,"YYYYY",yImageMax,yImageMean
		#print Y_IMAGEs

		LASTINGs=[]
		DISTs=[]
		SPEEDs=[]
		TRAILNESS=[]

		#print mover
		for k in  xrange(len(mover)-1):
			t=TIMEs[k+1]-TIMEs[k]
			LASTINGs.append(t)
			dis=Haversine((RAs[k+1]*pi/180,DECs[k+1]*pi/180),(RAs[k]*pi/180,DECs[k]*pi/180))*180/pi
			DISTs.append(dis)
			if t==0:
				speed=0
			else:
				speed=dis*3600*60/t
			SPEEDs.append(speed)



		meanSpeed=np.mean(SPEEDs)
		stdSpeed=np.std(SPEEDs)
		#print SPEEDs
		SPEEDs.append(SPEEDs[-1])

		TRAILNESS=map(lambda x:x/(meanSpeed*self.exposure/60),TRAILs)
		minTrail=min(TRAILNESS)
		maxTrail=max(TRAILNESS)
		if len(RAs)>2:
			#CORRELATION=lst[1][0]*3600*len(RAs)
			CORRELATION=lst[1][0]*3600
		else:
			CORRELATION=0

		meanSpeed=np.mean(SPEEDs)
		stdSpeed=np.std(SPEEDs)
	        f=lambda x:w[0]*x+w[1]
		cosfactor=np.cos(DECs[1]*np.pi/180)
		if (cosfactor==0):
			cosfactor=0.00001
		PA=np.arctan(w[0]/cosfactor)*180/np.pi

		if PA>=0:
			PA_ASTROMETRICA=PA
		else:
			PA_ASTROMETRICA=PA+360
 			
		#flags de deteccion 
		LINE_GOOD_DETECTION=1
		MAG_GOOD_DETECTION=2
		SP_GOOD_DETECTION=4
		CORRELATION_GOOD_DETECTION=8
		TRAILNESS_GOOD_DETECTION=16
		REAL_DETECTION=64

		if CORRELATION>float(cfg["min_correlation_coeff"]):
			CORRELATION_GOOD_DETECTION=0


		if minTrail <=float(cfg['min_trailness']) or maxTrail>=float(cfg['max_trailness']):
			TRAILNESS_GOOD_DETECTION=0
			#PEARL INDEX to chech if eclipse is pearled. TO BE DONE
			"""
			PAindex=int(PA)
			print PAindex,PA
			if PAindex-1 in self.pearlindex: 
				PAindex=PAindex-1
				print -1
			if PAindex+1 in self.pearlindex: 
				PAindex=PAindex+1
				print +1
			if PAindex in self.pearlindex: 
				self.pearlindex[PAindex]=self.pearlindex[PAindex]+1
			else:
				self.pearlindex[PAindex]=1
			if self.pearlindex[PAindex]==int(cfg['min_pearl_index']):
				TRAILNESS_GOOD_DETECTION=16
			"""

		ccd_line_flag=False
	        for i,mover_frame in enumerate(mover):
			#print mover_frame
			ra=RAs[i]
			dec=DECs[i]
			THETA=THETAs[i]
			if 0:
				print i,ra,dec,f(ra),(dec-f(ra))*3600,self.dis(ra,dec,w)*3600

			if abs(float(mover_frame['MAG_AUTO'])-meanmag_auto)>float(cfg["max_mag_diff"]):
				MAG_GOOD_DETECTION=0

			if abs(self.dis(ra,dec,w)*3600)>=float(cfg["max_rms_dis"]):		
				LINE_GOOD_DETECTION=0

			if abs((meanSpeed-SPEEDs[i])/meanSpeed)>float(cfg["max_speed_diff"]):			
				SP_GOOD_DETECTION=0



			"""
			if self.rotation < 0:
				rotation_reduced= 180+self.rotation 
			else:
				rotation_reduced= self.rotation

			pa_reduced=PA_ASTROMETRICA-rotation_reduced
			delta=float(cfg['ccd_lines_filter_diff'])
			ccd_line=  (-delta < pa_reduced < delta) or ( 180-delta < pa_reduced < 180+delta) 
			ccd_line_theta=  (-delta < THETA < delta) or ( 180-delta < THETA < 180+delta) 
			#print "ccd_line",self.rotation,rotation_reduced,PA_ASTROMETRICA,pa_reduced,ccd_line


			if cfg['ccd_lines_filter']  in ['True','true','yes','y'] and (ccd_line or ccd_line_theta) :
				print "CCD LINE POR PA!!!"
				ccd_line_flag=True
			"""
			
		CCDLineGauge=float(cfg['ccd_lines_filter_diff'])
		#print "CCD LINE TEST->",xImageMax,yImageMax
		if (xImageMax<=CCDLineGauge or yImageMax<=CCDLineGauge) and cfg['ccd_lines_filter']  in ['True','true','yes','y']:
				#print "CCD LINE POR GAUGE"
				ccd_line_flag=True

		if MAG_GOOD_DETECTION==0 or LINE_GOOD_DETECTION==0 or \
			CORRELATION_GOOD_DETECTION ==0 or SP_GOOD_DETECTION==0 or \
			TRAILNESS_GOOD_DETECTION==0:
				REAL_DETECTION=0

	
        	GOODFLAG=LINE_GOOD_DETECTION+MAG_GOOD_DETECTION+SP_GOOD_DETECTION+ \
			CORRELATION_GOOD_DETECTION+TRAILNESS_GOOD_DETECTION+REAL_DETECTION


        	#grabo los resultados en la lista 'rows'
		#if GOODFLAG==10:

	        for i,mover_frame in enumerate(mover):
			if (GOODFLAG>=64 and not ccd_line_flag ) or (cfg['do_not_filter'] in ['True','true','yes','y']) :
				print "REAL"
				ra=RAs[i]
				dec=DECs[i]
				pic=list(mover_frame)
				if i==0:
					IDNEW=self.designation()
					#IDNEW="DCMC%03u" % j
				print IDNEW
			 	pic.extend([SPEEDs[i],meanmag_auto,meanSpeed,stdSpeed,TRAILNESS[i],w[0],w[1],PA,PA_ASTROMETRICA, \
				self.dis(ra,dec,w)*3600,CORRELATION,GOODFLAG,IDNEW])
				#if GOODFLAG>=64:
				self.rows.append(pic)


				
	
	 header=self.cols
	 header.extend(self.addHeader)
	 header=[header]

	 if len(self.rows)==0:
		print "NO FASTMOVERS!"
		self.setStats('movers',0)
	    	return 0
	 else:
	 	with open(self.Fmovers.replace('cat','csv'), 'wb') as f:
			writer = csv.writer(f)
			writer.writerows(header)
			writer.writerows(self.rows)
	 	self.files_to_remove=self.files_to_remove+" "+self.Fmovers.replace('cat','csv')
	 	print "Writing fits cat"
		res=commands.getoutput("rm "+self.Fmovers)
	 	#stiltsStr="stilts tpipe ifmt=csv in=Gmovers_"+self.frame+".csv ofmt=fits-basic out="+self.Fmovers
		stiltsStr="stilts tpipe ifmt=csv in="+self.Fmovers.replace('cat','csv')+" ofmt=fits-basic \
			cmd='addcol OLDID (ID)' \
			cmd='delcols ID' \
			cmd='addcol ID (DESIGNATION)' \
			cmd='delcols DESIGNATION' \
			out="+self.Fmovers

	 	#print stiltsStr
	 	res=commands.getoutput(stiltsStr)
		print res
		self.clean()
		Nmovers=self.recordsInCAT(self.Fmovers)
		print "Creado:"+self.Fmovers+" N:"+str(Nmovers)
		self.matchMovers()
		self.setStats('movers',Nmovers)
		return Nmovers

	def clean(self):
 		res=commands.getoutput("rm "+self.files_to_remove)
		print res



  	def matchMovers(self):
		ok_sat_identification_dis=cfg['ok_sat_identification_dis']	
		sat_flag_cmd="addcol SAT_FLAG \"(DIS_SAT<"+str(ok_sat_identification_dis)+")\""	
		for i,sat in enumerate(self.sat_filtered):
			frame_cmd="select \"FRAME=="+str(i+1)+"\""
			stiltsStr="stilts tmatch2 \
			icmd1=\'"+frame_cmd+"\' \
 			find=best1 join=all1 in1="+self.Fmovers+"	\
			in2="+sat	+"\
			matcher=sky params="+cfg['max_sat_dis']+"  \
			values1=\"ALPHA_J2000 DELTA_J2000 \" \
			values2=\"RA DEC \" \
			suffix1='' suffix2='_SAT' \
			fixcols='all' \
			ocmd='addcol DIS_SAT \"(Separation)\"' \
			ocmd=\'"+ sat_flag_cmd+"\' \
			ocmd='delcols  \"Separation\"' \
			out=movers_sat_"+self.catalogs[i]+" ofmt=fits-basic"
			print 	"MATCHMOVERS",stiltsStr
			#stiltsStr=stiltsStr+" cmd='delcols 
			res=commands.getoutput(stiltsStr)
			print res


		cat_with_records=[]
		for (i,cat) in enumerate(self.catalogs): 
			if self.recordsInCAT("movers_sat_"+cat)>0:
				cols=self.columnsInCAT("movers_sat_"+cat)
				print "COLS:",cols
				#if cols==53:
				try:
		
					print "deleting GroupID,GroupSize"
					stiltsStr="stilts tpipe in=movers_sat_"+cat+" ofmt=fits-basic \
						  out=movers_sat_"+cat + \
						  " cmd='delcols GroupID ' cmd='delcols GroupSize'"
					print stiltsStr
					res=commands.getoutput(stiltsStr)
					print res
				except:
					pass

				cat_with_records.append("movers_sat_"+cat)
			
		#Las uno y un poco de housekeeping
		stiltsStr="stilts tcatn nin="+str(len(cat_with_records))+" out=G"+self.Fmovers+" ofmt=fits-basic   "
		for (i,cat) in enumerate(cat_with_records): 
			stiltsStr=stiltsStr+ " in"+str(i+1)+"="+cat +" "
		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res




if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	moverChecker=checkMovers(fitsFiles)
	moverChecker.do()
