#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Utility
#Generate catalog with a RA/DEC of all bodies
#in TLE database
#Input:Fit(s) files to read the time for the calculation
#Output:sat_{frame.cat
#invocation: 
#config file parameters:
#	Section:[OBSERVATORY]
#		lat,lon,elevation of the observatory
#
#	Section:[TLE]
#		tledir where to store TLEs 
#		tleurl where to get TLEs
#		max_dis search radius
#		ok_identification_dis below this consider sat matched 
#
#Nacho Mas Noviembre 2013
#Status: work


import ephem
import csv
import commands,os, sys
from math import *
import pyfits
import internetcatalogues
import zipfile
import urllib
import shutil
import eUcatalog
from PIL import Image,ImageDraw,ImageFont


from eUconfig import *
cfg=dict(config.items("TLE"))
cfgOBS=dict(config.items("OBSERVATORY"))

HTMLdir=cfg["base_html_dir"]
 
class SatPos(helper):
   files_to_remove=""


   def do(self):
	self.retriveTLEfile()
	self.SetObserver(lon=cfgOBS["lon"],lat=cfgOBS["lat"],elev=cfgOBS["elev"])
	
	for i,sat in enumerate(self.satOrbs):
		date=self.dates[i].replace('T',' ')
		print "FITS HEADER DATE:",date
		self.setDate(date)
		astPos=self.compute()
		print "Writing CSV"
		with open(sat, 'wb') as f:
		    writer = csv.writer(f)
		    writer.writerows(astPos)
  		self.files_to_remove=self.files_to_remove+" "+sat
		#print "Writing fits cat"
		#stiltsStr="stilts tpipe ifmt=csv in=astPos.csv ofmt=fits-basic out="+sat
		#print stiltsStr
		#res=commands.getoutput(stiltsStr)
		#print res
	self.filterTLEs()

	#CLEANNING
	#self.clean()

	return Nsats #return the number of matched satellites



   def SetObserver(self,lon,lat,elev,hor="00:00:00"):
     
      here = ephem.Observer()
      here.lat, here.lon, here.horizon  = str(lat), str(lon), str(hor)
      here.elev = float(elev)
      here.temp = 25e0
      here.compute_pressure()
      print("Observer info: \n", here)
      
      # setting in self
      self.here = here

   def setDate(self,date):
	self.here.date=ephem.date(date)+ephem.second*(self.exposure/2)
	print ephem.localtime(self.here.date)
        print("Observer info: \n", self.here)




   def compute(self):
	astPos=[["NAME","CAT_NUMBER","KEY","DATE","MAG","RA","DEC","AZ","ALT","RANGE","ELEVATION","RANGE_SPEED","ECLIPSED"]]
	#astPos=[["NAME","CAT_NUMBER","DATE","MAG","RA","DEC","AZ","ALT","RANGE","ELEVATION","RANGE_SPEED","ECLIPSED"]]
	failfile=cfg["failfile"]
	for i,tle in enumerate(self.TLEs):
		
		#print "Computing:",str(i),tle.name,
		tle.compute(self.here)
		#print ".",
		ra  =tle.ra*180/(pi)
		dec =tle.dec*180/pi
		dummy=self.TLE_IOs[i][1].split(' ')[2]
		if tle.range_velocity==0:
			print "FAIL to compute Sat:",dummy
			#continue
		if int(dummy[:2])>50:
			year='19'+dummy[:2]
		else:
			year='20'+dummy[:2]
		KEY=year+'-'+dummy[-4:]
		#print KEY
		#print "INT NUMBER",KEY,self.TLE_IOs[i][1]
		astPos.append((tle.name,tle.catalog_number,KEY,"{:18.11f}".format(self.here.date),tle.mag,ra,dec,tle.az*180/pi,tle.alt*180/pi,tle.range,tle.elevation,tle.range_velocity,tle.eclipsed))
		#astPos.append((tle.name,tle.catalog_number,self.here.date,tle.mag,ra,dec,tle.az*180/pi,tle.alt*180/pi,tle.range,tle.elevation,tle.range_velocity,tle.eclipsed))

	return astPos

   def retriveTLEfile(self):
	dir_dest=cfg["tledir"]
	if not os.path.exists(dir_dest):
		    os.makedirs(dir_dest)
	self.tlefile=dir_dest+'/'+self.getToday()+".TLE"
	#self.tlefile=dir_dest+'/13-12-07.TLE'
	print self.tlefile
	if not os.path.isfile(self.tlefile):
		print "TLE file not exit:",self.tlefile
		print "Downloading"
		res=commands.getoutput("wget -c "+cfg["tleurl"])
		print res
		print os.path.basename(cfg["tleurl"])
		res=commands.getoutput("unzip "+os.path.basename(cfg["tleurl"]))
		print res
		res=commands.getoutput("mv ALL_TLE.TXT "+self.tlefile)
		print res
		#Clasif TLE
		#http://www.prismnet.com/~mmccants/tles/classfd.zip
		print "Dowloading CLASIF TLE file:",cfg["tleclasifurl"]
		res=commands.getoutput("wget -c "+cfg["tleclasifurl"])
		print res
		print os.path.basename(cfg["tleclasifurl"])
		res=commands.getoutput("unzip "+os.path.basename(cfg["tleclasifurl"]))
		print res
		res=commands.getoutput("cat classfd.tle >> "+self.tlefile)
		print res



	i=internetcatalogues.internetCatalogue()
	self.TLEs=i.allTLE(self.tlefile,fromfile=True)
	self.TLE_IOs=i.TLE_IOs
	print "TLE from:",self.tlefile,"LOADED"
	print self.TLE_IOs[0]


   def filterTLEs(self):

	for i,sat in enumerate(self.satOrbs):
		(ra,dec)=self.centers[i]
		select_cone_cmd="select \"skyDistanceDegrees(RA,DEC,"+str(ra)+","+str(dec)+")<="+str(1+float(cfg['max_dis'])/3600)+"\""
		stiltsStr="stilts tpipe ifmt=csv in="+sat + "\
			cmd=\'"+ select_cone_cmd+"\' \
			ofmt=fits-basic out="+self.sat_filtered[i]
		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res


	"""
	(minRA,minDEC,maxRA,maxDEC)=self.maxBox()
	print "Filter TLE inside:RA",minRA,"-",maxRA,"DEC",minDEC,"-",maxDEC
	select_maxRA_cmd="select \"RA<="+str(maxRA+float(cfg['max_dis'])/3600)+"\""
	select_minRA_cmd="select \"RA>="+str(minRA-float(cfg['max_dis'])/3600)+"\""
	select_maxDEC_cmd="select \"DEC<="+str(maxDEC+float(cfg['max_dis'])/3600)+"\""
	select_minDEC_cmd="select \"DEC>="+str(minDEC-float(cfg['max_dis'])/3600)+"\""

	for i,sat in enumerate(self.satOrbs):
		stiltsStr="stilts tpipe ifmt=csv in="+sat + "\
			cmd=\'"+ select_maxRA_cmd+"\' \
			cmd=\'"+ select_minRA_cmd+"\' \
			cmd=\'"+ select_maxDEC_cmd+"\' \
			cmd=\'"+ select_minDEC_cmd+"\' \
			ofmt=fits-basic out="+self.sat_filtered[i]
		print 	stiltsStr
		res=commands.getoutput(stiltsStr)
		print res
	"""

  


   def clean(self):
		#return 0
 		res=commands.getoutput("rm "+self.files_to_remove)
		print res		

if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	fitFile=fitsFiles[0]
	#GEOSTATIONARY http://celestrak.com/NORAD/elements/geo.txt
#	url="http://www.idb.com.au/files/TLE_DATA/ALL_TLE.ZIP"

	sat=SatPos(fitsFiles)
	#sat.paintSats()
	sat.do()


