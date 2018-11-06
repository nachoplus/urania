#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#substract stars from source catalogue
#checking whether or not match between frames
#Input:list of source catalog files. 
#Output:same names but with 'loner_' file prefix
#	also a catalogue of stars in that field
#config file parameters:
#
#	Section:[LONERS]
#		seeing 
#		max_sex_flags
#
#Nacho Mas Junio 2013
#Status: work for La Sagra file

import pyfits
import commands,os, sys
import shutil
import re
import numpy as np
from eUconfig import *
cfg=dict(config.items("LONERS"))

class loners(helper):
    files_to_remove=""
    def do(self):
	print "FRAME:",self.frame
	#Creo una tabla con todos los catalogos
	#puedo filtrar pro el FLAG de sextrator
	stiltsStr="stilts tcatn nin="+str(len(self.catalogs))
	for (i,cat) in enumerate(self.catalogs):
	   stiltsStr=stiltsStr+ " in"+str(i+1)+"="+cat +"	"

	stiltsStr=stiltsStr+ " ocmd=\'select FLAGS<="+cfg["max_sex_flags"]+"\' "
	stiltsStr=stiltsStr+"loccol=\"frame\" out=fused_"+self.frame+".cat ofmt=fits-basic"
	print "Fusionando catalogos"
	print   stiltsStr
	res=commands.getoutput(stiltsStr)
	print res
	self.files_to_remove=self.files_to_remove+" fused_"+self.frame+".cat"

	#Detecto las fuentes que se repiten en todos los frame
	seeing=float(cfg["seeing"])
	select="select GroupSize>="+str(len(self.catalogs))
	stiltsStr="stilts tmatch1 matcher=sky values=\"ALPHA_J2000 DELTA_J2000\" params="+str(seeing)+" action=identify \
               ocmd=\'"+select+"\' in=fused_"+self.frame+".cat ofmt=fits-basic out=stars_"+self.frame+".cat"
	print "Identificando estrellas. Seeing:",cfg["seeing"]
	res=commands.getoutput(stiltsStr)
	print res

	#Creo catalogos con objetos unicos en el frame
	#Le quito los margenes y me quedo solo con las areas de solape
	margin_pix=int(cfg['margin_pix'])
	for (i,cat) in enumerate(self.catalogs):  
	   print ""	
	   print "FILE1:",cat
	   stiltsStr="stilts tmatch2  fixcols=none in1="+cat+ " in2=stars_"+self.frame+".cat matcher=sky params="+str(seeing)+" \
       		values1=\"ALPHA_J2000 DELTA_J2000\" \
       		values2=\"ALPHA_J2000 DELTA_J2000\" \
	        join=1not2  ocmd=\'select FLAGS<="+cfg["max_sex_flags"]+"\' \
		ocmd=\'select X_IMAGE>="+str(margin_pix)+"\' \
		ocmd=\'select X_IMAGE<="+str(self.frameWidth-margin_pix)+"\' \
		ocmd=\'select Y_IMAGE>="+str(margin_pix)+"\' \
		ocmd=\'select Y_IMAGE<="+str(self.frameHeight-margin_pix)+"\' \
		out="+self.loners[i]+"  ofmt=fits-basic"
		
	   print stiltsStr	
	   print "creando catalogo de loners %s"% (self.loners[i])
	   res=commands.getoutput(stiltsStr)
	   print res 
	   if os.path.isfile(self.loners[i]) and self.recordsInCAT(self.loners[i])!=0:	
	   	self.setStats('loners'+str(i),self.recordsInCAT(self.loners[i]))	
	   else:	
		self.setStats('loners'+str(i),"0")	
		return False

	#CLEANNING
	self.clean()
	return True

    def clean(self):
		#return 0
 		res=commands.getoutput("rm "+self.files_to_remove)
		print res

if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	Checker=loners(fitsFiles)
	Checker.do()

