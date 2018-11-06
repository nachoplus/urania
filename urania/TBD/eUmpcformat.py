#!/usr/bin/python
# -*- coding: utf-8 -*-
import ephem
import csv
import commands,os, sys
from math import *
import pyfits
import numpy as np

#http://www.minorplanetcenter.net/iau/info/OpticalObs.html

class MPCfile:
   header=['MPnumber','Provisional','Discovery','Note1','Note2','Date','RA','DEC','Mag','Band','Observatory']
   FITSformat=['5A','7A','1A','1A','1A','17A','12A','12A','5A','1A','3A']
   observations=[]
   def __init__(self):
	pass

   def read(self,filename):
      observation=[]
      MPC = open(filename, "r")
      n = 0
      for ast in MPC.readlines():
	if len(ast)!=81 and len(ast)!=82 :
		print "FAIL",len(ast)
		continue
	print ast[:-1]
        n += 1
        MPnumber=ast[0:5]
	Provisional=ast[5:12]
	Discovery=ast[12]
        Note1=ast[13]
        Note2=ast[14]
	Date=ast[15:32]
	RA=ast[32:44]
	DEC=ast[44:56]
	Mag=float(ast[65:70])
	Band=ast[70]
	Observatory=ast[77:80]

	obs=[MPnumber,Provisional,Discovery,Note1,Note2,Date,RA,DEC,Mag,Band,Observatory]

	observation.append(obs)
      print("\n Numero de observaciones:",n)

      self.observations.extend(observation)


   def writeMPC(self,filename):
      n = 0
      MPC = open(filename, "w")
      res=""
      for obs in self.observations:
        n += 1
	# ID a string,DEC con un solo decimal,mag con un solo decimal
	#print tuple(obs)
	#[MPnumber,Provisional,Discovery,Note1,Note2,Date,RA,DEC,Mag,Band,Observatory]
	#ast='%5s%07u%1s%1s%1s%17s%-12s%-12s         %5.1f%1s      %3s' % tuple(obs)
	ast='%5s%7s%1s%1s%1s%16s% -12s%-12s        %5.1f %1s      %3s' % tuple(obs)
	MPC.write(ast+'\n')
	res=res+ast+'\n'
	#print ast
      
      print "\n Numero de observaciones grabadas:",n
      MPC.close()		
      return res

   def writeCSV(self,filename):
	obs=[self.header]
	obs.extend(self.observations)
	with open(filename, 'wb') as f:
		writer = csv.writer(f)
		writer.writerows(obs)

   def writeFITs(self,filename):
	columns=[]
        
	for i,field in enumerate(self.header):
		a=np.array(map(lambda x:x[i],self.observations))
		col = pyfits.Column(name=field, format=self.FITSformat[i],array=a)
		columns.append(col)
	tbhdu = pyfits.new_table(columns)
	tbhdu.name='MPCObs'
	hdu = pyfits.PrimaryHDU() 
	hdulist = pyfits.HDUList([hdu, tbhdu])
	hdulist.info()
	hdulist.writeto(filename)

if __name__ == '__main__':
	mpc=MPCfile()
	fi=sys.argv[1:][0]
	print fi
	mpc.read(fi)
	mpc.writeCSV("lasagra.csv")
	mpc.writeMPC("lasagra.mpcobs")
	mpc.writeFITs("lasagra.cat")
