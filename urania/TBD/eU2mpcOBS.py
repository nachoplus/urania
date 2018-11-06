#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import pyfits
from pylab import *
import commands,os, sys
import shutil
import csv
import re
import numpy as np
from eUonfig import *
import eUcatalog

def do(cat):
	moverCAT=eUcatalog.moverCat()
	moverCAT.loadFIT(cat)
	moverCAT.writeMPC(frame+".mpcobs")


if __name__ == '__main__':
	print "FRAME:",frame
	cat="Gcandidates_S"+frame +".cat"
	do(cat)



	

	
