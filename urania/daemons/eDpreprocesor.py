#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing
#PREPROCESING MASTER DAEMON
#Look at the telescope direcories
#and launch the processing whe arrives
#Nacho Mas Oct 2013
#Status:

import shutil
from daemon import runner
import eUdaemon
import eUcleanheader

import eUcalibrate
import eUsolverAstrometry
import eUsolverScamp
import eUswarp
import eUhelper
import eUimager
import eSupernovaHunter

import eUsolverScamp

from eUconfig import *


class preprocesorDaemonClass(eUdaemon.FileChecker):

	def __init__(self):
		eUdaemon.FileChecker.__init__(self,section="PREPROCESOR_DAEMON")	

		self.stderr_path=self.cfg["log_dir"]+'/eDpreprocesor.log'
	        self.pidfile_path =  self.cfg["log_dir"]+'/eDpreprocesor.pid'
		log=self.getStats()
		log['PREPROCESOR_DAEMON_(RE)STARTED']=str(datetime.datetime.now())
		self.recordStats(log)

	def childInitDir(self):
		print "preprocesor day change function. Do nothing"
		pass


	def launch(self,dir_order__,dir,files):
		print "PREPROCESING:",dir,files

		self.solvedDirs=map(lambda x:x+"/"+self.getToday(),self.cfg["dir_solved"].split(','))

		dir_tmp=self.cfg['dir_tmp']
		if not os.path.exists(dir_tmp):
			    os.makedirs(dir_tmp)			

		for i,f in enumerate(files):
			shutil.copy(dir+"/"+f,dir_tmp+"/"+f)


		fits=map(lambda x:dir_tmp+"/"+x,files)
		h=eUhelper.helper(fits)
		dir_order=h.telescopesN[0]
		fits_type=h.fitstypes[0]
	
		#CALIBRATION
		cali=eUcalibrate.calibrator()
		if fits_type=='LASAGRA-RAW':
			cali.do(fits,telescopeN=dir_order,calibrate=True,invert=True)
		if fits_type=='LASAGRA-PINPOINT':
			cali.do(fits,telescopeN=dir_order,calibrate=False,invert=True)
		if fits_type=='EETF-ASTROMETRY':
			cali.do(fits,telescopeN=dir_order,calibrate=False,invert=False)


		#important clean after calibrate. Some bad header 
		cleaner=eUcleanheader.headerCleaner()
		cleaner.do(fits)
		
		#SOLVING
		#solver=eUsolverAstrometry.AstrometryNetSolver(fits)
		solver=eUsolverScamp.ScampSolver(fits)
		#EXIT if fail to solve
		if not solver.do():
			print "FAIL TO SOLVE"
			return fits_type+",FAIL TO SOLVE"

		#SWARP
		swarp=eUswarp.swarp(fits)
	   	#swarp.doOne2One()
		singlefit=swarp.doTriplet()	   	

		#make png images
		imager=eUimager.imagerClass(fits)
		imager.fitsPNGs()
		imager.writeRegistra()
		imager.paintNGCs()

		#tries supernova funtionality while doing is own daemon
		sn=eSupernovaHunter.SN_Hunter()
		sn.do(singlefit)

		#copy solvefits to all queues
		for k,queue in enumerate(self.cfg["dir_outbox"].split(',')):
		    dir_dest=queue+"/"+self.solvedDirs[dir_order]
		    if not os.path.exists(dir_dest):
				os.makedirs(dir_dest)
		    for i,f in enumerate(fits):
			ff=os.path.basename(f)
	
			#shutil.copy(f,dir_dest+"/"+ff)	
			#sextrator doesn't understand SIP distorsion factors
			#I use Russ Laher (PTF) conversion
			#
			if int(self.cfg["sip2pv"])==1:
				res=commands.getoutput("sip2pv -i "+f+" -o "+dir_dest+"/"+ff)
				if os.path.getsize(dir_dest+"/"+ff)==0:
					shutil.copy(f,dir_dest+"/"+ff)	
			else:
				print "PREPROCESOR: ",f,"TO: ",dir_dest+"/"+ff
				shutil.copy(f,dir_dest+"/"+ff)	
			#os.remove(f)
		shutil.rmtree(dir_tmp)
		return fits_type+",CLEANED,CALIBRATED,REGISTER"





if __name__ == '__main__':
	preprocesor=preprocesorDaemonClass()
	#preprocesor.run()
	daemon_runner = runner.DaemonRunner(preprocesor)
	daemon_runner.do_action()


