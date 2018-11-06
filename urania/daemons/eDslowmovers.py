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
import urllib
import eUdaemon


import eUsex
import eUloners

import eUmpcorb
import eAcandidates
import eAmovers
import eAcropper

import eUhelper

import eUimager


from eUconfig import *



class SlowMoverDaemonClass(eUdaemon.FileChecker):

	def __init__(self):
		eUdaemon.FileChecker.__init__(self,section="SLOWMOVER_DAEMON")	

		self.stderr_path = self.cfg["log_dir"]+'/eDslowmover.log'
		self.pidfile_path =  self.cfg["log_dir"]+'/eDslowmover.pid'

		log=self.getStats()
		log['SLOWMOVER_DAEMON_(RE)STARTED']=str(datetime.datetime.now())
		self.recordStats(log)

		#Check if there is a mpc_server configure. Start internal if not
		self.mpc_server=self.cfg['mpc_server']
		if len(self.mpc_server)==0:
			self.mpcEngine=eUmpcorb.MPCephem()

        def knowAsteroids(self,h):
           url=self.mpc_server
	   for i,fits in enumerate(h.solvefits):	
		print h.dates[i],h.mpc_filtered[i],h.centers[i][0],h.centers[i][1]
		date=h.dates[i].replace('T',' ')
		d = {}
		d['ra']  = h.centers[i][0]
		d['dec'] = h.centers[i][1]
		d['date'] = date
		d['r'] = 1.5
		d['format']="fits"
		url_values = urllib.urlencode(d)
		full_url = url + '?' + url_values
		urllib.urlretrieve(full_url,h.mpc_filtered[i])

	def childInitDir(self):
		#Download and filter MPCORB data
		if len(self.mpc_server)==0:
			print "Download and filter MPCORB data"
			self.mpcEngine.initEphem()

	def launch(self,dir_order,dir,fits):
		fits=map(lambda x:dir+x,fits)
		print "SEARCHING SLOWMOVERS:",fits
		self.dir_slowmovers=self.cfg["dir_slowmovers"]+'/'+self.getToday()

		h=eUhelper.helper(fits)
		frame=h.frame
		dir_order=h.telescopesN[0]
		dir_dest=self.dir_slowmovers+"/"+frame
		if not os.path.exists(dir_dest):
			print "CREATING:",dir_dest
		    	os.makedirs(dir_dest)			
		for f in h.solvefits:
			print "COPY",f
			shutil.copy(dir+f,dir_dest+"/"+f)

		os.chdir(dir_dest)


		imager=eUimager.imagerClass(fits)
		####### SLOWMOVERS ######
		sex=eUsex.sextractor(fits)
		sex.do("SEXASTEROIDS")

		#search asteroids in MPC data
		if len(self.mpc_server)==0:
			self.mpcEngine.triplet(fits)
		else:
			self.knowAsteroids(h)

		imager=eUimager.imagerClass(fits)
		imager.paintMPCs()


		lonerChecker=eUloners.loners(fits)
		lonerWork=lonerChecker.do()
		if not lonerWork:
			return 

		Acandidates=eAcandidates.candidates(fits)
		Ncandidates=Acandidates.do()
		if Ncandidates!=0:
			AmoverChecker=eAmovers.checkMovers(fits)
			Nmovers=AmoverChecker.do()
			if Nmovers!=0:
				imager.paintDetections("asteroid")
				cropper=eAcropper.cropClass(fits)
				cropper.loadCat()
				cropper.animations()
				response=cropper.writeJson()
				"""
				print "RESPONSE:",response
				slow_data_file=self.cfg['base_html_dir']+"/"+TodayDir()+"/slow_"+TodayDir()+".dat"
	        		fi=open(slow_data_file,"a")
				fi.write("FRAME:"+ h.frame)
				for keyA in response.keys:
					for key in response[keyA].keys:
						fi.write(response[key]+" ")
					fi.write("\n")
				fi.close()
				"""
				slow_json_file=self.cfg['base_html_dir']+"/"+TodayDir()+"/slow_"+TodayDir()+".json"
				json_dict=self.getStats(filename=slow_json_file)
				json_dict[frame]=response
				x = simplejson.dumps(json_dict)
	        		fi=open(slow_json_file,"w")
				fi.write(x)
				fi.close()



		#ERASE FITS 
		if int(self.cfg['delete_solved_fits']):
			for f in Acandidates.aperturesfiles:
				if  os.path.isfile(f):
					print "removing",f
					os.remove(f)
			for f in Acandidates.solvefits:
				if  os.path.isfile(f):
					print "removing",f
					os.remove(f)




		Jfilename=dir_dest+"/stats_"+frame+".json"	
		fi=open(Jfilename,"r")
		obj=fi.read()
		fi.close()
		result= simplejson.loads(obj)
		return result


if __name__ == '__main__':
	slowMover=SlowMoverDaemonClass()
	#slowMover.run()
	daemon_runner = runner.DaemonRunner(slowMover)
	daemon_runner.do_action()


