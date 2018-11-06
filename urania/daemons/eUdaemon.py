#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing
#BASE MASTER DAEMON
#Look at the telescope direcories
#and launch the processing whe arrives
#Nacho Mas Oct 2013
#Status:

import time
from daemon import runner
import os.path
import os
import glob
import datetime
import shutil
import simplejson


from eUconfig import *



class FileChecker(helper):

	def __init__(self,section=""):
		if len(section)==0:
			print "DAEMON BASE CLASS. NO SECTION DEFINED"
			exit(1)

		self.cfg=dict(config.items(section))
		if not os.path.exists(self.cfg["log_dir"]):
			os.makedirs(self.cfg["log_dir"])

		if not os.path.exists(self.cfg['base_html_dir']):
			os.makedirs(self.cfg["base_html_dir"])
			cmd="cp -av "+os.path.dirname(binpath)+"/html/controlpanel/* "+self.cfg['base_html_dir']
			res=commands.getoutput(cmd)
			print res

		self.initDir()
	        self.stdin_path = '/dev/null'
	        self.stdout_path = self.cfg['stdout']
	        self.stderr_path = '/dev/null'
	        self.pidfile_path =  '/tmp/eetfdaemon.pid'
	        self.pidfile_timeout = 5
		self.queued=0
		self.check_equal_size=True

	def initDir(self):
		self.checkDirs=self.cfg["dir_to_watch"].split(',')
		if self.cfg['append_date_to_dir_to_watch'] in ['True','true','yes','y']:
			self.checkDirs=map(lambda x:x+"/"+self.getToday()+"/"+self.cfg['dir_to_watch_posfix'],self.cfg["dir_to_watch"].split(','))
			#print self.checkDirs
		try:
			self.checkDirs.append(self.cfg['dir_reprocesor_queue'])
		except:
			print "No reprocesor queues configured"
		self.backupDirs=map(lambda x:x+"/"+self.getToday(),self.cfg["dir_backup"].split(','))
		self.file_pattern=self.cfg["file_pattern"]
		self.run_every=int(self.cfg["run_every"])
#		self.statsfile=self.cfg["stat_file"]
		dir_dest=os.path.dirname(self.cfg["stat_file"])+'/'+self.getToday()
		self.statsfile=dir_dest+'/'+os.path.basename(self.cfg["stat_file"])
		#print self.statsfile
		#things to do when the day change
		if not os.path.exists(dir_dest):
			os.makedirs(dir_dest)
			stats_files=os.path.dirname(binpath)+"/html/stats"
			res=commands.getoutput("cp -a "+stats_files+" "+dir_dest+"/.")
			writeCfg(dir_dest)
			print res
			#init child classes. This class has to be defined in every child
			self.childInitDir()

			

	def run(self):
        	while True:

			print "CHECKING FOR NEW ARRIVALS"
			self.initDir()
			T=datetime.datetime.now()
			print "TIME:",T
			self.free_disk(self.cfg["base_dir"])
			log=self.getStats()

			try:
				print "QUEUES:",log['QUEUES']
			except:
				log['QUEUES']=[0,0,0]
			try:
				print "DONE:",log['DONE']
			except:
				log['DONE']=[0,0,0]
			try:
				print "PROCESSED FRAMES:",len(log['FRAMES'])
			except:
				log['FRAMES']=[]


			for i,dir in enumerate(self.checkDirs):
				f=dir+"/"+self.file_pattern
				print "searching for...",f
				files=glob.glob(f)	
				fits=self.checkReadyFrames(dir,files)
				log['DATE']=T.strftime('%d/%m/%Y %H:%M:%S')
				#BE AWARE HARDCODE NUMBER OF QUEUES
				if i<3:
					log['QUEUES'][i]=self.queued
	 			self.recordStats(log)
				if fits:
					frame=fits[0][:-7]
					print T,"FRAME:%s HAS ARRIVED FROM:%s!!" % (frame,dir)
					T0=datetime.datetime.now()
					self.backup(i,dir,fits)
					response=self.launch(i,dir,fits)
					#response="TEST"
					T1=datetime.datetime.now()
					#log=self.getStats()
					statdata={'CENTU':i,'FRAME':frame,'START_TIME':T0.strftime('%d/%m/%Y %H:%M:%S'),\
						'END_TIME':T1.strftime('%d/%m/%Y %H:%M:%S'),'ETA':str(T1-T0), \
						'LAUNCH_RESPONSE':response}
					log['FRAMES'].append(statdata)
					if not self.cfg['keep'] in ['True','true','yes','y']:
						for f in fits:
							os.remove(dir+"/"+f)
					if i<3:
						log['DONE'][i]=int(log['DONE'][i])+1
						log['QUEUES'][i]=self.queued-1
					self.recordStats(log)

				else:
					print dir," Not data"
			self.recordStats(log)
			print "Sleeping.."
			print ""
        		time.sleep(self.run_every)

	def checkReadyFrames(self,dir,files): 
		files=map(lambda x:os.path.basename(x),files)
		frames=set(map(lambda x:x[:-7],files))
		self.queued=len(frames)
		#print "files:",files
		#print "Frames",frames
		for frame in frames:
			#print frame
			if not self.waitReadyAuxFiles(dir,frame):
				print "Wait for aux files"
				return False
			frameset=filter(lambda x:x.startswith(frame),files)
			#print "FILES:",len(frameset),int(self.cfg['wait_for_n_files'])
			if len(frameset)>=int(self.cfg['wait_for_n_files']):		
				sizes=set(map(lambda x:int(os.path.getsize(dir+"/"+x)/(1048576)),frameset))
				#print sizes,len(sizes)
				if self.check_equal_size:	
					if len(sizes)==1 and sizes.pop()>=1:
						return sorted(frameset)
				else:
					return sorted(frameset)
		return False



	def waitReadyAuxFiles(self,dir,frame): 
		if self.cfg["aux_file_pattern"]=="":
				return True
		check_equal_size=False
		self.aux_file_pattern=map(lambda x:x+frame+"*.cat",self.cfg["aux_file_pattern"].split(','))
		#print "Searching aux files:",self.aux_file_pattern,len(self.aux_file_pattern)
		for aux_mask in self.aux_file_pattern:
			f=dir+aux_mask
			#print "auxiliary files MASK:",f
			files=glob.glob(f)	
			#print "aux files",files
			files=map(lambda x:os.path.basename(x),files)
			#print "FILES:",len(files),int(self.cfg['wait_for_n_files'])
			if len(files)>=int(self.cfg['wait_for_n_files']):		
				sizes=set(map(lambda x:int(os.path.getsize(dir+"/"+x)/1048576),files))
				#print sizes,len(sizes)
				if check_equal_size:	
					if not(len(sizes)==1 and sizes.pop()>=1):
						return False
				else:
					continue
			else:
				return False
		return True



	def backup(self,dir_order,dir,fits):
		#BE AWARE HARDCODE NUBER OF QUEUES
		if not self.cfg['backup']in ['True','true','yes','y'] or dir_order>=3:
			return
		dir_dest=self.backupDirs[dir_order]
		if not os.path.exists(dir_dest):
		    	os.makedirs(dir_dest)			
		for i,f in enumerate(fits):
			shutil.copy(dir+"/"+f,dir_dest+"/"+f)



	def recordStats(self,jsn):
		filename=self.statsfile
		x = simplejson.dumps(jsn)
		statsDir=os.path.dirname(filename)
		if not os.path.exists(statsDir):
		    os.makedirs(statsDir)
	        fi=open(filename,"w")
		fi.write(x)
		fi.close()
		#print  jsn


	def launch(self,dir_order,dir,fits):
		print "Doing nothing:",dir,fits
		return "Doing nothing:"

	def free_disk(self,dire):
		disk = os.statvfs(dire)
		totalAvailSpaceNonRoot = float(disk.f_bsize*disk.f_bavail)
		print "available space %.2f GBytes " % (totalAvailSpaceNonRoot/1024/1024/1024)


if __name__ == '__main__':
	checker=FileChecker(section="PREPROCESOR_DAEMON")
	#checker.run()
	daemon_runner = runner.DaemonRunner(checker)
	daemon_runner.do_action()


