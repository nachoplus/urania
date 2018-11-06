#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing
#PREPROCESING MASTER DAEMON
#Look at the telescope direcories
#and launch the processing whe arrives
#Nacho Mas Oct 2013
#Status:

import shutil,os
from daemon import runner

import eUdaemon
import urllib

import eUtle
import eUsex
import eUloners
import eFcandidates
import eFmovers
import eFcropper


import eUhelper

import eUimager

from eUconfig import *


class fastMoverDaemonClass(eUdaemon.FileChecker):

	def __init__(self):
		eUdaemon.FileChecker.__init__(self,section="FASTMOVER_DAEMON")	
		self.stderr_path = self.cfg["log_dir"]+'/eDfastmover.log'
		self.pidfile_path =  self.cfg["log_dir"]+'/eDfastmovers.pid'

		log=self.getStats()
		log['FASTMOVER_DAEMON_(RE)STARTED']=str(datetime.datetime.now())
		self.recordStats(log)

		self.sat_server=self.cfg['sat_server']

        def knowSats(self,h):
           url=self.sat_server
	   for i,fits in enumerate(h.solvefits):	
		print h.dates[i],h.sat_filtered[i],h.centers[i][0],h.centers[i][1]
		date=h.dates[i].replace('T',' ')
		d = {}
		d['ra']  = h.centers[i][0]
		d['dec'] = h.centers[i][1]
		d['date'] = date
		d['r'] = 1.5
		d['format']="fits"
		url_values = urllib.urlencode(d)
		full_url = url + '?' + url_values
		urllib.urlretrieve(full_url,h.sat_filtered[i])

	def childInitDir(self):
		print "fastmover day change function. Do nothing"
		#SATs are init on invocation
		#Sat=eUtle.SatPos()/home/nacho/work/TYCHO_SOFT/bin/eDfastmovers.py
		#Sat.retriveTLEfile()
		pass



	def launch(self,dir_order,dir,fits):
		fits=map(lambda x:dir+x,fits)
		print "SEARCHING FASTMOVERS:",fits
		self.dir_fastmovers=self.cfg["dir_fastmovers"]+'/'+self.getToday()

		h=eUhelper.helper(fits)
		frame=h.frame
		dir_order=h.telescopesN[0]
		dir_dest=self.dir_fastmovers+"/"+frame
		if not os.path.exists(dir_dest):
			print "CREATING:",dir_dest
		    	os.makedirs(dir_dest)			
		for f in h.solvefits:
			print "COPY",f
			shutil.copy(dir+f,dir_dest+"/"+f)


		os.chdir(dir_dest)
		#iraf.chdir(dir_dest)

		imager=eUimager.imagerClass(fits)
		####### FASTMOVERS ######

		if len(self.sat_server)==0:
			#Search know satellites
			Sat=eUtle.SatPos(fits)
			Nsats=Sat.do()
		else:
			self.knowSats(h)

		imager.paintSats()
			
		#sources
		sex=eUsex.sextractor(fits)
		sex.do("SEXFAST")

		#CALL AFTER sex (before aperture files do not exist)
		imager.aperturesPNGs()

		lonerChecker=eUloners.loners(fits)
		lonerWork=lonerChecker.do()
		if not lonerWork:
			return 

		Fcandidates=eFcandidates.candidates(fits)
		Ncandidates=Fcandidates.do()

		if Ncandidates!=0:
			FmoverChecker=eFmovers.checkMovers(fits)
			Nmovers=FmoverChecker.do()
		else:
			Nmovers=0

		#WORK ARROUND FOR MOVE PICTURES OR RARE. MEJOR EN CANDIDATES
		if Nmovers>=30:
			Nmovers=0
			
		if Nmovers!=0:
			imager.paintDetections("fastmover")		
			Fcropper=eFcropper.cropClass(fits)
			Fcropper.do()


		#ERASE FITS AND APERTURE IF NOT DETECTIONS
		#if Nmovers==0:
		if int(self.cfg['delete_solved_fits']):
			for f in Fcandidates.aperturesfiles:
				if  os.path.isfile(f):
					print "removing",f
					os.remove(f)
			for f in Fcandidates.solvefits:
				if  os.path.isfile(f):
					print "removing",f
					os.remove(f)


		#self.mermaid.html()
		Jfilename=dir_dest+"/stats_"+frame+".json"	
		fi=open(Jfilename,"r")
		obj=fi.read()
		fi.close()
		result= simplejson.loads(obj)
		return result


if __name__ == '__main__':
	fastMover=fastMoverDaemonClass()
	#fastMover.run()
	daemon_runner = runner.DaemonRunner(fastMover)
	daemon_runner.do_action()


