#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import pyfits
import commands,os, sys
import shutil
import csv
import re
import numpy as np
import eUmpcformat

class Cat:
	data=[]
	header=[]
	cols=[]


	def loadFIT(self,filename):
		hdulist = pyfits.open(filename)
		#hdulist.info()
		self.header = hdulist[1].columns
		self.cols = self.header.names
		self.data = hdulist[1].data

	def addCol(self,colname,coldata):
		if len(coldata)!=len(data):
			print ""

	def saveFIT(self,filename):
		columns=[]
		for i,field in enumerate(self.header):
			print i,field.name
			col = pyfits.Column(name=field.name, format=field.format)
			columns.append(col)
		tbhdu = pyfits.new_table(columns)
		tbhdu.name='DATA'
		tbhdu.data=self.data
		hdu = pyfits.PrimaryHDU() 
		hdulist = pyfits.HDUList([hdu, tbhdu])
		hdulist.info()
		hdulist.writeto(filename)

class moverCat(Cat):

	def toMPCobs(self,ID=0):
	    observations=[]	
	    if ID==0:
		daton=self.data
	    else:
		daton=filter(lambda x:x['ID']==ID,self.data)

	    for row in daton:
		fecha=row['DATETIME'][0:10].replace('-',' ')
		hh=float(row['DATETIME'][11:13])
		mm=float(row['DATETIME'][14:16])
		ss=float(row['DATETIME'][17:19])
		print "CHECKSEC",row['DATETIME'],ss
		hhdecInt=int(((hh+mm/60.+ss/3600.)/24.)*100000.)
		hhdec=round((hh*3600.+mm*60.+ss)/(24*3600)*100000,0)
		print hhdecInt,hhdec
		fecha=fecha+'.'+"%05.0f" % (hhdec)+" "
		#print '.'+"%05.0f" % (hhdec)+" "
		#print row['DATETIME'],hh,mm,ss
	        MPnumber=''
		Provisional=row['ID']
		Discovery=' '
	        Note1=' '
	        Note2='C'
		Date=fecha
		RA=row['RA'].replace(' ','').replace(':',' ')
		DEC=row['DEC'].replace(' ','').replace(':',' ')
		DEC=DEC[:-1]
		Mag=int(float(row['MAG_AUTO'])*10.)/10.
		Band='V'
		Observatory='J75'
		obs=[MPnumber,Provisional,Discovery,Note1,Note2,Date,RA,DEC,Mag,Band,Observatory]
		observations.append(obs)
	    return observations


	def loadFromMPCobs(self,filename):
		mpc=eUmpcformat.MPCfile()	
		mpc.read(filename)
		mod_obs=[]
		#[MPnumber,Provisional,Discovery,Note1,Note2,Date,RA,DEC,Mag,Band,Observatory]
		for obs in mpc.observations:
			fecha=obs[5][0:10].replace(' ','-')
			fraccion=float("."+obs[5][11:])
			hora_dec=fraccion*24
			hora=int(hora_dec)
			minuto_dec=(hora_dec-hora)*60
			minuto=int(minuto_dec)
			segundo=(minuto_dec-minuto)*60
			obs[5]="%s %02d:%02d:%06.3f" % (fecha,hora,minuto,segundo)
			#print obs[5]
			obs[6]=obs[6].strip().replace(' ',':')
			obs[7]=obs[7].strip().replace(' ',':')
			mod_obs.append(obs)
		mpc.observations=mod_obs
		mpc.header[1]="ID"
		mpc.header[5]="DATETIME"
		mpc.FITSformat[5]="22A"
		mpc.header[8]="MAG_AUTO"	
		mpc.writeFITs(filename+".cat")
		self.loadFIT(filename+".cat")

			
		

	def writeMPC(self,filename,ID=0):
		mpc=eUmpcformat.MPCfile()
		mpc.observations=self.toMPCobs(ID)
		return mpc.writeMPC(filename)
		

if __name__ == '__main__':
	fi=sys.argv[1:][0]
	print fi
	moverCAT=moverCat()
	moverCAT.loadFromMPCobs(fi)
	moverCAT.writeMPC("lasagra2.mpcobs")



	

	
