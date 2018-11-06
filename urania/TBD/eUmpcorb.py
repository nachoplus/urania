#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Utility
#Generate catalog with a RA/DEC of all bodies
#in MPC database
#Input:Fit(s) files to read the time for the calculation
#Output:astPOS{datetime}.cat
#invocation: 
#config file parameters:
#	Section:[OBSERVATORY]
#		lat,lon,elevation of the observatory
#
#	Section:[MPCORB]
#		mpcorb.dat to be used
#Nacho Mas Junio 2013
#Status: work

import ephem
import csv
import commands,os, sys
from math import *
import simplejson
import pyfits
import urllib

from eUconfig import *
cfg=dict(config.items("MPCORB"))
cfgOBS=dict(config.items("OBSERVATORY"))


def give_number(letter):
    
    try:
     int(letter)
     return letter
    except ValueError:
     if letter.isupper():
      return str(ord(letter) - ord('A') + 10)
     if letter.islower():
      return str(ord(letter) - ord('a') + 36)

def convert_design(packed):

  '''
    Convert the packed designation format to formal designation.
  '''

  isdigit = str.isdigit

  try:
    packed = packed.strip()
  except ValueError:
    print("ValueError: Input is not convertable to string.")

  if isdigit(packed) == True: desig = packed.lstrip('0') # ex: 00123
  
  if isdigit(packed[0]) == False: # ex: A7659 = 107659

    if isdigit(packed[1:]) == True: # ex: A7659
      desig = give_number(packed[0]) + packed[1:]
      
    elif isdigit(packed[1:3]) == True:  # ex: J98SG2S = 1998 SS162
    
      if isdigit(packed[4:6]) == True and packed[4:6] != '00':
        desig = give_number(packed[0]) + packed[1:3] + ' ' + packed[3] + packed[-1] + packed[4:6].lstrip("0")
        
      if isdigit(packed[4:6]) == True and packed[4:6] == '00':
        desig = give_number(packed[0]) + packed[1:3] + ' ' + packed[3] + packed[-1]
        
      if isdigit(packed[4:6]) == False:
        desig = give_number(packed[0]) + packed[1:3] + ' ' + packed[3] + packed[-1] + give_number(packed[4]) + packed[5]
      
    elif packed[2] == 'S': # ex: T1S3138 = 3138 T-1     
      desig = packed[3:] + ' ' + packed[0] + '-' + packed[1]
  
  return desig

def convert_date(packdt):

  '''
    Convert the packed year format to standard year.
  '''
  
  try:
    packdt = str(packdt).strip()
  except ValueError:
    print("ValueError: Input is not convertable to string.")    
  
  '''  
     Month     Day      Character         Day      Character
                     in Col 4 or 5              in Col 4 or 5
   Jan.       1           1             17           H
   Feb.       2           2             18           I
   Mar.       3           3             19           J
   Apr.       4           4             20           K
   May        5           5             21           L
   June       6           6             22           M
   July       7           7             23           N
   Aug.       8           8             24           O
   Sept.      9           9             25           P
   Oct.      10           A             26           Q
   Nov.      11           B             27           R
   Dec.      12           C             28           S
             13           D             29           T
             14           E             30           U
             15           F             31           V
             16           G

   Examples:

   1996 Jan. 1    = J9611
   1996 Jan. 10   = J961A
   1996 Sept.30   = J969U
   1996 Oct. 1    = J96A1
   2001 Oct. 22   = K01AM
  '''
  
  return '/'.join([give_number(packdt[0]) + packdt[1:3],give_number(packdt[3]),give_number(packdt[4])])


class MPCorbEphem:
   asteroid=dict()
   filter_asteroid=dict()
   sun = ephem.Sun()


   def LoadMPCorb(self,filename):
      asteroid=dict()
      MPC = open(filename, "r")
      n = 0
      for ast in MPC.readlines():
        n += 1
        if n > 41:

	   try:
               H=float(ast[8:12]),
               G=float(ast[15:19]),
               asteroid[ast[:7]] = tuple(ast[8:104].split())
	   except:
	       asteroid[ast[:7]] = tuple([0e0,0.15]+ast[20:104].split())

      print "\n MPC catalogue has been read. The total of asteroids fullfilling the conditions are ",len(asteroid), " of ",n-43

      # setting in self:
      #print asteroid	
      self.asteroid = asteroid


   def SetObserver(self,lat,lon,elev,hor="10:00:00"):
     
      here = ephem.Observer()
      here.lat, here.lon, here.horizon  = str(lat), str(lon), str(hor)
      here.elev = float(elev)
      here.temp = 25e0
      here.compute_pressure()
      print "Observer info: \n", here
      
      # setting in self
      self.here = here

   def setDate(self,date):
	self.here.date=ephem.date(date)
	print ephem.localtime(self.here.date)
        print("Observer info: \n", self.here)
	self.sun.compute(self.here)  

   def setDateFromFIT(self,fitsfile):
	hdulist = pyfits.open(fitsfile)
	hdr = hdulist[0].header
	try:
	        date=hdr['DATE-OBS']
	except:
		try:
			date=hdr['DATE']
		except:
			print "FITS NOT CONTAING DATE/DATE-OBS KEY"
			exit(0)
	date=date.replace('T',' ')
	print "Date from",fitsfile,"FITS HEADER:",date
	self.setDate(date)
	return date
      
   def LoadObject(self,des):
     
      '''
         Input: asteroid Designation (des).
         Output: Return pyephem class with asteroid ephemeris for any date or observer.
      '''
      
      
      ast = ephem.EllipticalBody()
      
      '''
      EllipticalBody elements:

       _inc — Inclination (°)
       _Om — Longitude of ascending node (°)
       _om — Argument of perihelion (°)
       _a — Mean distance from sun (AU)
       _M — Mean anomaly from the perihelion (°)
       _epoch_M — Date for measurement _M
       _size — Angular size (arcseconds at 1 AU)
       _e — Eccentricity
       _epoch — Epoch for _inc, _Om, and _om
       _H, _G — Parameters for the H/G magnitude model
       _g, _k — Parameters for the g/k magnitude model
      '''      
      
      # Reading
      H, G, epoch_M, M, argper, node, i, e, n, a = self.asteroid[des]
      
      # Asteroid Parameters
      ast._H, ast._G, ast._M, ast._om, ast._Om, ast._inc, ast._e, ast._a = map(float,[H,G,M,argper,node,i,e,a])
      ast._epoch_M = str(convert_date(epoch_M))
      #print ast._H, ast._G, ast._M, ast._om, ast._Om, ast._inc, ast._e, ast._a	
      #print convert_date(epoch_M)

      # Constants
      ast._epoch = str("2000/1/1 12:00:00")

      return ast

   def phase_angle(self,elongation, earthd, sund):
   
	r = self.sun.earth_distance
	ratio = (earthd**2 + sund**2 - r**2)/(2e0*earthd*sund)
	ph_rad = acos(round(ratio,5))
	return degrees(ph_rad)



   def vmag(self,H,G,phang,delta,r):
        
	phang = phang*pi/180e0
    
    	# Constants
    	A1 = 3.332; A2 = 1.862
    	B1 = 0.631; B2 = 1.218
    	#C1 = 0.986; C2 = 0.238
    
	# phase functions
   	f = lambda A, B, ph: exp((-A)*tan(5e-1*ph)**B) + 1e-10

    	# reduced magnitude
    	rmag =  H - 2.5*log10((1 - G)*f(A1,B1,phang) + G*f(A2,B2,phang))
    
    	# apparent visual magnitude
    	return rmag + 5*log10(r*delta)

   def compute(self):
	astPos=[["KEY","DATE","OBS_DATE","RA","DEC","MAG","PHASE","EARTH_DIS","SUN_DIS","ELONG","SUN_SEPARATION"]]
	for key, value in self.filter_asteroid.iteritems() :
		    try:	
		    	obs_date=str(convert_date(value[2]))
			a=self.LoadObject(key)
			a.compute(self.here)
			ra  =a.a_ra*180/(pi)
			dec =a.a_dec*180/pi
			phang=self.phase_angle(a.elong,a.earth_distance,a.sun_distance)
			vmag=self.vmag(a._H,a._G,phang,a.earth_distance,a.sun_distance)
			sun_separation=ephem.separation(self.sun,a)
			astPos.append((key,str(self.here.date),obs_date,ra,dec,vmag,phang,a.earth_distance,a.sun_distance,a.elong,sun_separation))

		    except:
			print key," fail"	
	return astPos






class MPCephem(MPCorbEphem,helper):

    def __init__(self):
	lon=cfgOBS["lon"]
	lat=cfgOBS["lat"]
	elev=cfgOBS["elev"]
	self.SetObserver(lon,lat,elev)
	self.json_file=cfg["mpcorb_filters_dir"]+"/mpc_filter_"+"_"+TodayDir().replace('-','_')+".json"
	if not os.path.isfile(self.json_file):
		print "NO EXISTS:",self.json_file
		print "prefiltring mpcorb positions"
		self.initEphem()


    def initEphem(self):
	self.retriveMPCORBfile()
	self.LoadMPCorb(self.mpcorbfile)
	date="20"+TodayDir()+" 00:00"
	self.setDate(date)
	self.filter_asteroid=self.asteroid
	astPos=self.compute()
	#self.writeOBS(astPos,"ALL"+TodayDir().replace('-','_')+".mpc")
	self.ORBmainFilter(astPos)
	self.json_file=cfg["mpcorb_filters_dir"]+"/mpc_filter_"+"_"+TodayDir().replace('-','_')+".json"
	self.save_filter_asteroid()
	return astPos 
	

    def writeOBSfilter(self,pos,filename,ra,dec):	
	#TODO Now fix radius, read cfg to do the cone search
	select_cone_cmd="select \"skyDistanceDegrees(RA,DEC,"+str(ra)+","+str(dec)+")<1.5"+"\""
	filename_csv=filename.replace("cat","csv")
	print "Writing CSV",filename_csv
	print len(pos)
	if len(pos)==1:
		print "No MPC in field.Exitting"
		return
	with open(filename_csv, 'wb') as f:
	    writer = csv.writer(f)
	    writer.writerows(pos)
	print "Writing fits cat",filename
	stiltsStr="stilts tpipe ifmt=csv in="+filename_csv+"\
			cmd=\'"+ select_cone_cmd+"\' \
			ofmt=fits-basic out="+filename
	print stiltsStr
	res=commands.getoutput(stiltsStr)
	print res
	os.remove(filename_csv)
	print res

    def writeOBS(self,pos,filename_):	
	#filename_ arg with extension
	filename=filename_+".csv"
	print "Writing CSV"
	with open(filename, 'wb') as f:
	    writer = csv.writer(f)
	    writer.writerows(pos)
	print "Writing fits cat"
	stiltsStr="stilts tpipe ifmt=csv in="+filename+"\
			ofmt=fits-basic out="+filename.replace("csv","cat")
	#print stiltsStr
	res=commands.getoutput(stiltsStr)
	os.remove(filename)
	print res

    def ORBmainFilter(self,pos):
	maxMag=float(cfg["maxmag"])
	minSunSep=float(cfg["sunsep"])*15*pi/180
	filterlist=filter(lambda x:x[5]<=maxMag,pos)
	filterlist=filter(lambda x:x[10]>=minSunSep,filterlist)
	filterkeys=map(lambda x:x[0],filterlist)
	print "FILTERED:",len(filterkeys)
	self.filter_asteroid = { key: self.asteroid[key] for key in filterkeys }

    def save_filter_asteroid(self):
	filename=self.json_file
	json=simplejson.dumps(self.filter_asteroid)
	statsDir=os.path.dirname(filename)
	if not os.path.exists(statsDir):
		    os.makedirs(statsDir)
        fi=open(filename,"w")
	fi.write(json)
	fi.close()

    def load_filter_asteroid(self):
	filename=self.json_file
	if not os.path.isfile(filename):
		print "NO EXISTS:",filename
		self.initEphem()
	    	return {}
	fi=open(filename,"r")
	obj=fi.read()
	fi.close()
	self.asteroid= simplejson.loads(obj)
	self.filter_asteroid=self.asteroid


    def retriveMPCORBfile(self):
	dir_dest=cfg["mpcorbpath"]
	if not os.path.exists(dir_dest):
		    os.makedirs(dir_dest)
	if len(cfg['force_mpcorb_file'])==0:
		self.mpcorbfile=dir_dest+'/'+TodayDir()+".mpcorb"
	else:
		self.mpcorbfile=dir_dest+'/'+cfg['force_mpcorb_file']

	print self.mpcorbfile
	if not os.path.isfile(self.mpcorbfile):
		print "MPCORB file not exit:",self.mpcorbfile
		print "Downloading"
		filename=os.path.basename(cfg["mpcorburl"])
		print filename
		cmd="wget -c "+cfg["mpcorburl"]+" -O "+cfg['mpcorbpath']+"/"+filename
		print cmd
		res=commands.getoutput(cmd)
		print res
		res=commands.getoutput("gunzip -f "+cfg['mpcorbpath']+"/"+filename)
		print res
		res=commands.getoutput("mv "+cfg['mpcorbpath']+"/"+filename.replace(".gz","")+ " "+self.mpcorbfile)
		print res

    def do(self,fitsFile):
	pass

    def triplet(self,fitsFile):
	helper.__init__(self,fitsFile)
	if len(self.asteroid)==len(self.filter_asteroid):
		self.load_filter_asteroid()
	for i,fits in enumerate(fitsFile):
		date=self.setDateFromFIT(fits)
		pos=self.compute()
		print self.mpc_filtered[i],self.centers[i][0],self.centers[i][1]
	        self.writeOBSfilter(pos,self.mpc_filtered[i],self.centers[i][0],self.centers[i][1])	





if __name__ == '__main__':
	mpc=MPCephem()
	pos=mpc.initEphem()
	#mpc.load_filter_asteroid()
	#mpc.triplet(sys.argv[1:])

	pos=mpc.compute()
	mpc.writeOBS(pos,"ALL_MPC_"+TodayDir().replace('-','_'))

	

