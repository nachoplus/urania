#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#Filter candidates searching for real movers
#Input:'Gcandidates_'{framename}.cat
#Output:same names but with 'Gmover_' file prefix
#config file parameters:
#
#	Section: [AMOVERS]
#		min_correlation_coeff
#		mpc_dis
#		max_mag_diff
#		max_mag_diff_mpc
#		max_rms_dis
#		max_speed_diff
#
#Nacho Mas Junio 2013
#Status: work. Further housekeeping needed


import pyfits
from pylab import *
import commands,os, sys
import shutil
import csv
import re
import numpy as np
import eUcatalog

from eUconfig import *
cfg=dict(config.items("AMOVERS"))
debug=cfg["debug"]

def Debug(string):
	if debug in ['True','true','yes','y']:
		print string

class checkMovers(eUcatalog.moverCat,helper):
	addHeader=(["speed","pmRA","pmDEC","MEAN_MAG","MEANSpeed","stdSpeed","PA","RMS","CORRELATION_RA","CORRELATION_DEC","GOODFLAG","KNOW","DESIGNATION"])
	rows=[]
	files_to_remove=" "
	#distancia de un punto (ra,dec) a una recta de coeficientes w (a=w[0],b=w[1])
	def dis(self,ra,dec,w):
		return (w[0]*ra-dec+w[1])/(w[0]*w[0]+1)

	def matchMPC(self):	
	  	lista=[]
	  	for i,mpc in enumerate(self.mpc_filtered):
			Pmover="P"+str(i)+self.Amovers
			if not os.path.isfile(mpc):
				continue
			frame_cmd="select  \"FRAME=="+str(i+1)+"\"" 
			stiltsStr="stilts tmatch2 find=best1 join=all1 in1="+self.Acandidates+"	\
			in2="+mpc+ "	\
			matcher=sky params="+cfg['mpc_dis_check']+"  \
			values1=\"ALPHA_J2000 DELTA_J2000 \" \
			values2=\"RA DEC \" \
			suffix1='' suffix2='_MPC' \
			fixcols='all' \
			ocmd=\'"+frame_cmd+ "\' \
			ocmd='addcol DIS_MPC \"(Separation)\"' \
			ocmd='delcols Separation' \
			out="+Pmover+" ofmt=fits-basic"
			print 	stiltsStr
			res=commands.getoutput(stiltsStr)
			self.files_to_remove=self.files_to_remove+" "+Pmover
			lista.append(Pmover)
			print res


		#Join the tables
		if len(lista)==0:
			#IF NOT RESULT COPY THE ORIGINAL FILE
			if not os.path.isfile("P"+self.Amovers):
				res=commands.getoutput("cp P"+self.Amovers+" "+self.Amovers)
		else:
			stiltsStr="stilts tcatn nin="+str(len(lista))+" out=P"+self.Amovers+" ofmt=fits-basic  ocmd='sort ID' "
			for (i,cat) in enumerate(lista): 
				stiltsStr=stiltsStr+ " in"+str(i+1)+"="+cat +" "
			res=commands.getoutput(stiltsStr)
			print res
			self.files_to_remove=self.files_to_remove+" P"+self.Amovers


	def getMPCnotMatched(self):	
	  	lista=[]
	  	for i,mpc in enumerate(self.mpc_filtered):
			Pmover="N"+str(i)+self.Amovers
			if not os.path.isfile(mpc):
				continue
			frame_cmd="select  \"FRAME=="+str(i+1)+"\"" 
			stiltsStr="stilts tmatch2 find=best1 join=2not1 in1="+self.Amovers+"	\
			in2="+mpc+ "	\
			matcher=sky params="+cfg['mpc_dis']+"  \
			values1=\"ALPHA_J2000 DELTA_J2000 \" \
			values2=\"RA DEC \" \
			ocmd='addcol FRAME \"("+str(i+1)+")\"' \
			ocmd='addcol ALPHA_J2000 \"(RA)\"' \
			ocmd='delcols RA' \
			ocmd='addcol DELTA_J2000 \"(DEC)\"' \
			ocmd='delcols DEC' \
			ocmd='addcol ID \"(KEY)\"' \
			ocmd='delcols KEY' \
			out="+Pmover+" ofmt=fits-basic"
			print 	stiltsStr
			res=commands.getoutput(stiltsStr)
			self.files_to_remove=self.files_to_remove+" "+Pmover
			lista.append(Pmover)
			print res


		#Join the tables
		if len(lista)==0:
			#IF NOT RESULT COPY THE ORIGINAL FILE
			pass
		else:
			stiltsStr="stilts tcatn nin="+str(len(lista))+" out=N"+self.Amovers+" ofmt=fits-basic  "
			for (i,cat) in enumerate(lista): 
				stiltsStr=stiltsStr+ " in"+str(i+1)+"="+cat +" "
			res=commands.getoutput(stiltsStr)
			print res
			self.files_to_remove=self.files_to_remove+" N"+self.Amovers



	def do(self):
 	 self.rows=[]
	 self.matchMPC()
	 if not os.path.isfile("P"+self.Amovers):
		print "NO SLOW MOVERS!"
		return 0	
	 self.loadFIT("P"+self.Amovers)

	 movers=self.data
	 moversIDs=set(movers['ID'])
	 #print moversIDs
	 self.rows=[]
	 for moverID in moversIDs:
		moverFlt=(movers['ID']==moverID)
		mover=movers[moverFlt]
		#print  moverFlt,mover
		#mover=sorted(mover,key=lambda mover:mover['MJDATE'])
	
		mag_auto=map(lambda x:float(x['MAG_AUTO']),mover)
		meanmag_auto=np.mean(mag_auto)
		stdmag_auto=np.std(mag_auto)


		RAs=map(lambda x:float(x['ALPHA_J2000']),mover)
		x=RAs

		DECs=map(lambda x:float(x['DELTA_J2000']),mover)
		y=DECs

		MJDATEs=map(lambda x:float(x['MJDATE']),mover)
		mjd=np.array([MJDATEs,np.ones(len(MJDATEs))]).T

		pmRAs=[]
		pmDECs=[]
		speeds=[]
		###Calculo velocidades
	        for i,mover_frame in enumerate(mover):
			if i+1 >=len(mover):
				#pmRAs.append(pmRAs[i-1])
				#pmDECs.append(pmDECs[i-1])
				#speeds.append(speeds[i-1])
				break
			ra0=RAs[i]
			dec0=DECs[i]
			t0=MJDATEs[i]
			ra1=RAs[i+1]
			dec1=DECs[i+1]
			t1=MJDATEs[i+1]
			#SPEEDs in arcseg/min
			pmRA=((ra1-ra0)*3600*cos(dec0*pi/180))/((t1-t0)*24*60)
			pmDEC=((dec1-dec0)*3600)/((t1-t0)*24*60)
			speed=math.sqrt(pmRA*pmRA+pmDEC*pmDEC)
			pmRAs.append(pmRA)
			pmDECs.append(pmDEC)
			speeds.append(speed)


		pmRAs=np.array(pmRAs)
		pmDECs=np.array(pmDECs)
		speeds=np.array(speeds)
		meanSpeed=np.mean(speeds)
		stdSpeed=np.std(speeds)


		X_IMAGEs=map(lambda x:float(x['X_IMAGE']),mover)
		xImageMean=np.mean(X_IMAGEs)
		xImageStd=np.std(X_IMAGEs)
		xImageMax=np.max(map(lambda x:x-xImageMean,X_IMAGEs))

		Y_IMAGEs=map(lambda x:float(x['Y_IMAGE']),mover)
		yImageMean=np.mean(Y_IMAGEs)
		yImageStd=np.std(Y_IMAGEs)
		yImageMax=np.max(map(lambda x:x-yImageMean,Y_IMAGEs))


		###Ajuste de una recta por minimos cuadrados
		print mjd
		print x
		print y
		lst = np.linalg.lstsq(mjd,x)
		w_ra=lst[0]
		CORRELATION_RA=lst[1][0]
		Debug("RA CORRELATION")
		Debug("COEFF:"+str(w_ra))
		Debug("CORRELATION:"+str(CORRELATION_RA))
		#funcion de la recta
	        f_ra=lambda x:w_ra[0]*x+w_ra[1]


		lst = np.linalg.lstsq(mjd,y)
		w_dec=lst[0]
		CORRELATION_DEC=lst[1][0]
		Debug("DEC CORRELATION")
		Debug("COEFF:"+str(w_dec))
		Debug("CORRELATION:"+str(CORRELATION_DEC))
		#funcion de la recta
	        f_dec=lambda x:w_dec[0]*x+w_dec[1]

		CORRELATION=CORRELATION_DEC*CORRELATION_RA

		#RMS ERROR 
		err=0
		for ii in xrange(0,3):
			time=MJDATEs[ii]	
			_ra=f_ra(time)
			_dec=f_dec(time)
			print time, _ra,RAs[ii],_ra-RAs[ii]
			print time, _dec,DECs[ii],_dec-DECs[ii]
			delta= (_ra*np.cos(_dec*np.pi/180)-RAs[ii]*np.cos(DECs[ii]*np.pi/180))**2+(_dec-DECs[ii])**2
			print delta
			err=err+delta

		rms=np.sqrt(err/3)*3600
		print "RMS:",rms
		
                if 1:
			pendiente=w_dec[0]/w_ra[0]
			#PA=np.arctan(pendiente)*180/np.pi+90

			cosfactor=cos(DECs[1]*np.pi/180)
			if (cosfactor==0):
				cosfactor=0.00001
			PA=180/np.pi*(np.arctan(pendiente/cosfactor))
	
			if pmRAs[0]<0:
				PA_ASTROMETRICA=270-PA
			else:
				PA_ASTROMETRICA=90-PA
		

		#flags de deteccion 
		LINE_GOOD_DETECTION=1
		MAG_GOOD_DETECTION=2
		SP_GOOD_DETECTION=4
		CORRELATION_GOOD_DETECTION=8
		MPC_GOOD_DETECTION=16
		MPC_MAG_GOOD_DETECTION=32
		REAL_DETECTION=64
		KNOW=1

		if CORRELATION>float(cfg["min_correlation_coeff"]):
			CORRELATION_GOOD_DETECTION=0

		if isnan(mover[0]['DIS_MPC']) or mover[0]['DIS_MPC']>=float(cfg["mpc_dis"]):
			MPC_GOOD_DETECTION=0
			KNOW=0

		if isnan(mover[0]['MAG_MPC']) or (float(mover['MAG_AUTO'][0])-mover[0]['MAG_MPC'])>float(cfg["max_mag_diff_mpc"]):
			MPC_MAG_GOOD_DETECTION=0

		CCDLineGauge=float(cfg['ccd_lines_filter_diff'])
		ccd_line_flag=False
		#print "CCD LINE TEST->",xImageMax,yImageMax
		if (xImageMax<=CCDLineGauge or yImageMax<=CCDLineGauge) and cfg['ccd_lines_filter']  in ['True','true','yes','y']:
				print "CCD LINE GAUGE",moverID
				ccd_line_flag=True

	        for i,mover_frame in enumerate(mover):
			#print mover_frame
			ra=RAs[i]
			dec=DECs[i]

			if abs((float(mover_frame['MAG_AUTO'])-meanmag_auto))>float(cfg["max_mag_diff"]):
				MAG_GOOD_DETECTION=0

			if abs(rms)>=float(cfg["max_rms_dis"]):			
				LINE_GOOD_DETECTION=0

			if i!=2 and abs((meanSpeed-speeds[i])/meanSpeed)>float(cfg["max_speed_diff"]):			
				SP_GOOD_DETECTION=0

		if MAG_GOOD_DETECTION==0 or LINE_GOOD_DETECTION==0 or CORRELATION_GOOD_DETECTION ==0 or ccd_line_flag or SP_GOOD_DETECTION==0:
			REAL_DETECTION=0
	
        	GOODFLAG=LINE_GOOD_DETECTION+MAG_GOOD_DETECTION+SP_GOOD_DETECTION+CORRELATION_GOOD_DETECTION+MPC_GOOD_DETECTION+MPC_MAG_GOOD_DETECTION+REAL_DETECTION


        	#grabo los resultados en la lista 'rows'
		#if GOODFLAG==10:

	        for i,mover_frame in enumerate(mover):
			if REAL_DETECTION!=0:
			#if not ccd_line_flag:
				if i==0:
					IDNEW=self.designation(slow=True)
				print IDNEW
				ra=RAs[i]
				dec=DECs[i]
				pic=list(mover_frame)

				if i==2:
					sp_=0
					sp_ra_=0
					sp_dec_=0
				else:
					sp_=speeds[i]
					sp_ra_=pmRAs[i]
					sp_dec_=pmDECs[i]

			 	pic.extend([sp_,sp_ra_,sp_dec_,meanmag_auto,meanSpeed,stdSpeed, \
					PA_ASTROMETRICA,rms,CORRELATION_RA,CORRELATION_DEC,GOODFLAG,KNOW,IDNEW])
		        	Debug(pic)
				self.rows.append(pic)
	
	 if len(self.rows)==0:
		 print "NO SLOWMOVERS!"
		 self.setStats('movers',0)
		 self.clean()
	    	 return 0
	 else:
		 header=self.cols
		 header.extend(self.addHeader)
		 header=[header]
		 #print header
		 with open(self.Amovers.replace('cat','csv'), 'wb') as f:
			writer = csv.writer(f)
			writer.writerows(header)
			writer.writerows(self.rows)
		 self.files_to_remove=self.files_to_remove+" "+self.Amovers.replace('cat','csv')
		 print "Writing fits cat"
		 res=commands.getoutput("rm "+self.Amovers)
		 stiltsStr="stilts tpipe ifmt=csv in="+self.Amovers.replace('cat','csv')+" ofmt=fits-basic \
			cmd='addcol OLDID (ID)' \
			cmd='delcols ID' \
			cmd='addcol ID (DESIGNATION)' \
			cmd='delcols DESIGNATION' \
			out="+self.Amovers
		 #print stiltsStr
		 res=commands.getoutput(stiltsStr)
		 print res

		 #create knowmovers
		 print "Writing KNOWMOVERS"
		 knowobs=eUcatalog.moverCat()
		 knowobs.loadFIT(self.Amovers)
		 knowobs.data=filter(lambda x:x['KNOW']==1,knowobs.data)
		 res=commands.getoutput("rm "+self.Aknowmovers)
		 knowobs.writeMPC(self.Aknowmovers)
		 knowfile=os.path.dirname(cfg['knowfile'])+"/"+TodayDir()+"/"+os.path.basename(cfg['knowfile'])
		 print "Append know to:",knowfile
		 with open(self.Aknowmovers, 'r') as content_file:
		    content = content_file.read()
		 fio=open(knowfile,"a")
 		 fio.write(content)
		 fio.close()

		 #create unknowmovers
		 print "Writing UNKNOWMOVERS"
		 unknowobs=eUcatalog.moverCat()
		 unknowobs.loadFIT(self.Amovers)
		 unknowobs.data=filter(lambda x:x['KNOW']==0,unknowobs.data)
		 res=commands.getoutput("rm "+self.Aunknowmovers)
		 unknowobs.writeMPC(self.Aunknowmovers)
		 unknowfile=os.path.dirname(cfg['unknowfile'])+"/"+TodayDir()+"/"+os.path.basename(cfg['unknowfile'])
		 print "Append unknow to:",unknowfile
		 with open(self.Aunknowmovers, 'r') as content_file:
		    content = content_file.read()
		 fio=open(unknowfile,"a")
 		 fio.write(content)
		 fio.close()

		 Nmovers=self.recordsInCAT(self.Amovers)
		 print "Creado:"+self.Amovers+" N:"+str(Nmovers)
		 self.setStats('movers',Nmovers)
		 self.clean()
		 return Nmovers

		
	 self.clean()

	def clean(self):
		print "Removing tmp files:",self.files_to_remove
 		res=commands.getoutput("rm "+self.files_to_remove)
		print res



if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	moverChecker=checkMovers(fitsFiles)
	#moverChecker.getMPCnotMatched()
	moverChecker.do()
