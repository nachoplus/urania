#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing
#HELPER
#Input:Fits files
#Nacho Mas Octubre 2013
#Status: 

#Configuration file

import commands,os, sys
import datetime
from eUconfig import *
import simplejson

import numpy
import wcsutil
import pyfits




class helper:
	type=""
	frameWidth=""
	frameHeight=""
	exposure=""
	fits=""
	catalogs=""
	loners=""
	candidates=""
	movers=""
	def __init__(self,argu):
		self.cfg=dict(config.items("HELPER"))
		self.type=self.cfg["frametype"]


		#self.do_not_solve=cfg["do_not_solve"] in ['True','true','yes','y']
		#self.check_mpc=cfg["check_mpc"] in ['True','true','yes','y']

		#self.todaydate=self.getToday()
		self.workingPath=os.path.dirname(argu[0])
		self.fits=sorted(map(lambda x:os.path.basename(x),argu))

		if self.type=='LASAGRA':
			self.frame=self.fits[0][:-7]

		if self.type=='RAMONNAVES':
			#frame=fitsFiles[0][:-14]      #C2011K5
			self.frame=fitsFiles[0][:-6]        #C2009P1

		#if self.do_not_solve :
		self.basedir=os.path.dirname(self.fits[0])
		if self.basedir=='':
			self.basedir='./'
		self.solvefits=self.fits
		#else:
		#	self.solvefits=map(lambda x:"S"+x,self.fits)

		self.statsfile="stats_"+self.frame+".json"
		self.catalogs=map(lambda x:x.replace(".fit",".cat"),self.fits)
		self.pngs=map(lambda x:x.replace(".fit",".png"),self.fits)
		self.jpegs=map(lambda x:x.replace(".fit",".jpg"),self.fits)
		self.loners=map(lambda x:"loners_"+x,self.catalogs)
		self.triloners=map(lambda x:"triloners_"+x,self.catalogs)
		self.Fcandidates='Fcandidates_'+self.frame+'.cat'
		self.Fmovers='Fmovers_'+self.frame+'.cat'
		self.Acandidates='Acandidates_'+self.frame+'.cat'
		self.Amovers='Amovers_'+self.frame+'.cat'
		self.Aknowmovers='Aknowmovers_'+self.frame+'.mpcobs'
		self.Aunknowmovers='Aunknowmovers_'+self.frame+'.mpcobs'
		self.aperturesfiles=map(lambda x:"apertures_"+x,self.fits)
		self.pngsApertures=map(lambda x:x.replace(".fit",".png"),self.aperturesfiles)
		self.satOrbs=map(lambda x:"sat_"+x.replace(".fit",".csv"),self.fits)
		self.sat_filtered=map(lambda x:"sat_filtered_"+x.replace(".fit",".cat"),self.fits)
		self.mpc=map(lambda x:"mpc_"+os.path.basename(x).replace(".fit",".csv"),self.fits)
		self.mpc_filtered=map(lambda x:"mpc_filtered_"+os.path.basename(x).replace(".fit",".cat"),self.fits)

		self.names={'frame':self.frame,'fits':self.fits,'solvefits':self.solvefits, \
			'catalogs':self.catalogs,'loners':self.loners,'triloners':self.triloners, \
			'Fcandidates':self.Fcandidates, 'Fmovers':self.Fmovers,'apertures':self.aperturesfiles}

		self.basicFitData()


	def getNames(self,what):
		return self.names[what]


	def getToday(self):
		return TodayDir()




	def designation(self,teles="",order=0,slow=False):
		teleN=""
		if teles=="":	
			if self.telescope=='OLS-Centurion1':
				teles='X'
				teleN='CENTU1'

			if self.telescope=='OLS-Centurion2':
				teleN="CENTU2"
				teles='Y'

			if self.telescope=='OLS-Centurion3':
				teles='Z'
				teleN='CENTU3'

		if slow:
			teleN=teleN+"SLOW"
		print self.telescope,teles,teleN
		if order==0:
			order=self.getCurrentID(teleN)
		today = datetime.datetime.now()

		#For ours propouse we change the day at noon
		today=today-datetime.timedelta(hours=int(self.cfg["day_change_at"])) 

		runningYear=today.year-2010
		if runningYear>9:
			year_cod=chr(runningYear+55)
		else:
			year_cod=chr(runningYear+48)

		if today.month>9:
			month_cod=chr(today.month+55)
		else:
			month_cod=chr(today.month+48)
		if today.day>9:
			day_cod=chr(today.day+55)
		else:
			day_cod=chr(today.day+48)

		orderDec= order % 100 #Last 2 digits
		orderCen= int(order/100)

		if orderCen>9:
			Zletter=chr(orderCen+55)
		else:
			Zletter=chr(orderCen+48)
			
		return year_cod+month_cod+day_cod+teles+ "%s" % Zletter +"%02i" % orderDec



	def give_number(letter):
    	    	try:
    		 int(letter)
    		 return letter
    		except ValueError:
			if letter.isupper():
		      		return str(ord(letter) - ord('A') + 10)
			if letter.islower():
		      		return str(ord(letter) - ord('a') + 36)

	def update_hdr(self,fits,name,value,comment=""):
		import pyfits
		hdulist = pyfits.open(fits,mode='update')
		#hdulist.info()
		header = hdulist[0].header
		if isinstance(value, str):
			value=value.strip()
			print value
		header[name]=(value,comment)
		#print header
		hdulist.close()

	def del_hdr(self,fits,name):
		import pyfits
		hdulist = pyfits.open(fits,mode='update')
		header = hdulist[0].header
		del header[name]
		hdulist.close()

	##BASIC FIT FRAME DATA
	def basicFitData(self):
	    import pyfits
	    self.frameWidths=[]
 	    self.frameHeights=[]
	    self.exposures=[]
	    self.dates=[]
	    self.telescopes=[]
	    self.telescopesN=[]
	    self.fitstypes=[]
            self.rotations=[]
            self.arcsecperpixs=[]
            self.centers=[]
            for i,fits in enumerate(self.solvefits):
		hdulist = pyfits.open(os.path.join(self.workingPath,fits))
		#hdulist.info()
		header = hdulist[0].header
		self.frameWidths.append(header['NAXIS1'])
		self.frameHeights.append(header['NAXIS2'])
		try:
			self.exposures.append(header['EXPOSURE'])
		except:
			try:	
				self.exposures.append(header['EXPTIME'])
			except:
				print "Falta el tiempo de exposicion en el FITs"
				exit(1)
		try:
			self.dates.append(header['DATE-OBS'])
		except:
			print "Falta la fecha en el FITs"
			exit(1)

		try:
			telescopeN=-1
			telescope=header['TELESCOP']
			self.telescopes.append(telescope)
			if telescope=='OLS-Centurion1':
				teles='A'
				teleN='CENTU1'
				telescopeN=0

			if telescope=='OLS-Centurion2':
				teleN="CENTU2"
				teles='B'
				telescopeN=1

			if telescope=='OLS-Centurion3':
				teles='C'
				teleN='CENTU3'
				telescopeN=2

			self.telescopesN.append(telescopeN)
	
		except:
			print "Falta la cabecera del telescopio"

		try:
			self.rotations.append(header['ROTATION'])
		except:
			self.rotations.append(0)
			print "Missing rotation header. Setting to 0"
		try:
			#dummy=str(header['COMMENT'])
			#self.arcsecperpixs.append(float(dummy[dummy.find('scale:'):].split('\n')[0].split(' ')[1]))
			self.arcsecperpixs.append(header['PIXSCALE'])
		except:
			self.arcsecperpixs.append(1.94845)
			print "Missing scale. Using hardcode 1.948"
		try:
			dummy=str(header['COMMENT'])
			if dummy.find('--Start of Astrometry.net WCS solution--')!=-1:
				self.fitstypes.append('EETF-ASTROMETRY')				
			else:
				raise Exception("No astrometry.net")
		except:
			try:
				dummy=str(header['HISTORY'])
				if dummy.find('PinPoint')!=-1:
					self.fitstypes.append('LASAGRA-PINPOINT')
			except:
				self.fitstypes.append('LASAGRA-RAW')


		try:
			(ra,dec)=self.pix2wcs(os.path.join(self.workingPath,fits),(self.frameWidths[i]/2,self.frameHeights[i]/2))
			self.centers.append((ra,dec))
		except:
			print "Fail to calculating RA/DEC of center!!"
			self.centers.append((float('NaN'),float('NaN')))

	    self.frameWidth=self.frameWidths[0]
 	    self.frameHeight=self.frameHeights[0]
	    self.exposure=self.exposures[0]
	    self.telescope=self.telescopes[0]
            self.rotation=self.rotations[0]
            self.arcsecperpix=self.arcsecperpixs[0]





		#return {"frameWidth":frameWidth,"frameHeight":frameHeight,"exposure":exposure}



	def recordsInCAT(self,cat):
		import pyfits
		hdulist = pyfits.open(cat)
		nrecords=hdulist[1].header['NAXIS2']
		hdulist.close()
		return int(nrecords)



	def columnsInCAT(self,cat):
		import pyfits
		hdulist = pyfits.open(cat)
		ncolumns=hdulist[1].header['TFIELDS']
		hdulist.close()
		return int(ncolumns)

	def getMJDATEInCAT(self,cat):
		import pyfits
		hdulist = pyfits.open(cat)
		date=hdulist[1].data['MJDATE'][0]
		hdulist.close()
		return date


	def setStats(self,parameter,value,filen=''):
		if filen=='':
			filen=self.statsfile
		json_dict=self.getStats(filename=filen)
		json_dict[parameter]=value
		x = simplejson.dumps(json_dict)
	        fi=open(filen,"w")
		fi.write(x)
		fi.close()
		#print  json_dict	

	def getStats(self,filename=''):
		if filename=='':
			filename=self.statsfile
		if not os.path.isfile(filename):
			print "NO EXISTS:",filename
		    	return {}
	        fi=open(filename,"r")
		obj=fi.read()
		fi.close()
		json_dict= simplejson.loads(obj)
		return json_dict


	def getCurrentID(self,telescope):
		dir_dest=os.path.dirname(self.cfg["current_designator_file"])+'/'+self.getToday()
		stat_file=dir_dest+'/'+os.path.basename(self.cfg["current_designator_file"])
		if not os.path.isfile(stat_file):
			print "DESIGNATOR FILE NOT EXISTS:",stat_file
			print "INIT DESIGNATIONS..."
			Dcentu1=1
			Dcentu2=1
			Dcentu3=1
			json_dict={'CENTU1':Dcentu1,'CENTU2':Dcentu2,'CENTU3':Dcentu3,'CENTU1SLOW':Dcentu1,'CENTU2SLOW':Dcentu2,'CENTU3SLOW':Dcentu3}
			x = simplejson.dumps(json_dict)
		        fi=open(stat_file,"w")
			fi.write(x)
			fi.close()

		print "Designations from:",stat_file
		stats=self.getStats(filename=stat_file)
		print stats
		ID=int(stats[telescope])
		stats[telescope]=int(ID)+1
		x = simplejson.dumps(stats)
		print telescope,stats
	        fi=open(stat_file,"w")
		fi.write(x)
		fi.close()			
		return ID


	def wcs2pix(self,fits,(ra,dec)):
		try:
			return wcs2pix(fits,(ra,dec))
		except numpy.linalg.linalg.LinAlgError as err:
			return self.KKwcs2pix(fits,(ra,dec),distort=False)


	def pix2wcs(self,fits,(x,y)):
		try:
			return pix2wcs(fits,(x,y))
		except:
			return self.KKpix2wcs(fits,(x,y),distort=False)


	def KKwcs2pix(self,fits,(ra,dec),distort=True):
		if distort:
			cmd='wcs-rd2xy -w '+fits+" -r "+str(ra)+" -d "+str(dec)
		else:
			cmd='wcs-rd2xy -t -w '+fits+" -r "+str(ra)+" -d "+str(dec)
		#print cmd
		res=commands.getoutput(cmd)
		#print res
		try:
			res=res.split('(')[2][:-1].split(',')
			x=float(res[0])
			y=float(res[1])
		except:
			x=0
			y=0

		return (x,y)


	def KKpix2wcs(self,fits,(x,y),distort=True):
		if distort:
			cmd='wcs-xy2rd -w '+fits+" -x "+str(x)+" -y "+str(y)
		else:
			cmd='wcs-xy2rd -t -w '+fits+" -x "+str(x)+" -y "+str(y)
		res=commands.getoutput(cmd)
		res=res.split('(')[2][:-1].split(',')
		ra=float(res[0])
		dec=float(res[1])
		return (ra,dec)

	def maxBox(self):
		for i,fits in enumerate(self.solvefits):
			(ra0,dec0)=self.pix2wcs(fits,(0,0))
			(ra1,dec1)=self.pix2wcs(fits,(self.frameWidths[i],self.frameHeights[i]))
			(ra2,dec2)=self.pix2wcs(fits,(self.frameWidths[i],0))
			(ra3,dec3)=self.pix2wcs(fits,(0,self.frameHeights[i]))
			maxRA=max(ra0,ra1,ra2,ra3)
			minRA=min(ra0,ra1,ra2,ra3)
			maxDEC=max(dec0,dec1,dec2,dec3)
			minDEC=min(dec0,dec1,dec2,dec3)
			#WORKARROUND TO AVOID NEAR ARIES POINT INCONSISTENCES
			if (maxRA-minRA) >200:
				return 0,0,0,0
			else:
				return minRA,minDEC,maxRA,maxDEC	


def getcenterRADEC(fit):	
	hdulist = pyfits.open(fit)
	hdulist.verify('silentfix')  
	header = hdulist[0].header
	Width=int(header['NAXIS1'])
	Height=int(header['NAXIS2'])
	hdulist.close()
	(ra,dec)=pix2wcs(fit,(Width/2,Height/2))
	return (ra,dec)

def pix2wcs(fits,(x,y)):
	# Load the FITS hdulist using pyfits
	hdulist = pyfits.open(fits)
	hdulist.verify('silentfix')  
	try:
		# Parse the WCS keywords in the primary HDU
		wcs = wcsutil.WCS(hdulist[0].header)
	except numpy.linalg.linalg.LinAlgError as err:
	  if 'Singular matrix' in err.message:
	    	# your error handling block
		print "Singular matrix, not distorsion will be consider"
		raise
	  else:
	   	raise
		
	(ra,dec) = wcs.image2sky(x,y)
	return (ra,dec)

def wcs2pix(fits,(ra,dec)):
	# Load the FITS hdulist using pyfits
	hdulist = pyfits.open(fits)
	hdulist.verify('silentfix')  
	try:
		# Parse the WCS keywords in the primary HDU
		wcs = wcsutil.WCS(hdulist[0].header)
	except numpy.linalg.linalg.LinAlgError as err:
	  if 'Singular matrix' in err.message:
	    	# your error handling block
		print "Singular matrix, not distorsion will be consider"
		raise
	  else:
	   	raise

	(x,y) = wcs.sky2image(ra,dec)
	return (x,y)


if __name__ == '__main__':
	h=helper(sys.argv[1:])
	print "FRAME:",h.getNames('frame')
	print "DATE:",h.getToday()
	print "FITs:",h.getNames('fits')
	print "Solve FITs:",h.getNames('solvefits')
	print "Catalog Files:",h.getNames('catalogs')
	print "Loners Files:",h.getNames('loners')
	#print "Candidates Files:",h.getNames('candidates')
	#print "Movers Files:",h.getNames('movers')
	print h.centers,h.rotations,h.arcsecperpixs,h.exposures,h.dates
	print "sizes:",h.frameWidth,h.frameHeight
	print "FIT-TYPES:",h.fitstypes





