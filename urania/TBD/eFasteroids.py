#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#Main task
#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#Main task

import sys,os

import eUsex
import eUimager
import eUloners
import eUtle
import eFcandidates
import eFmovers
import eFcroppies
from eUconfig import *

class FastMoverSearcher:

	def do(self,fitsFiles):

		if 1:
			sex=eUsex.sextractor(fitsFiles)
			sex.do("SEXFAST")

			#make png images
			#imager=eUimager.imagerClass(fitsFiles)
			#imager.aperturesPNGs()

			lonerChecker=eUloners.loners(fitsFiles)
			lonerChecker.do()

			candidates=eFcandidates.candidates(fitsFiles)
			Ncandidates=candidates.do()
			#Sat=eUtle.SatPos(fitsFiles)
			#Nsats=Sat.do()

			if Ncandidates!=0:
				moverChecker=eFmovers.checkMovers(fitsFiles)
				Nmovers=moverChecker.do()
			else:
				Nmovers=0
			###CHAPUZA LIMITE PARA FOTOS MOVIDAS o RARAS. MEJOR EN CANDIDATES
			if Nmovers>=30:
				Nmovers=0

		if 1:
			if Nmovers==0:
		            #if Nsats<0: 
		            #if Nsats==0: 
				for f in candidates.aperturesfiles:
					print "removing",f
					os.remove(f)
				for f in candidates.solvefits:
					print "removing",f
					os.remove(f)
			    #return (Ncandidates,0)			
			else:
				cropper=eFcroppies.cropClass(fitsFiles)
				cropper.do()
			

			return (Ncandidates,Nmovers)

if __name__ == '__main__':
	fits=sys.argv[1:]
	searcher=FastMoverSearcher()
	searcher.do(fits)
