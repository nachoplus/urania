#!/usr/bin/python
# -*- coding: iso-8859-15 -*-



import commands,os, sys

from eUconfig import *

cfg=dict(config.items("SWARP"))

class swarp(helper):
	def doTriplet(self):
		lista=" "
		for i,fit in enumerate(self.solvefits):
			lista=lista+" "+fit
		path=cfg['dir_swarp_base']+'/'+self.getToday()+'/swarp'
		if not os.path.exists( path):
    			os.makedirs(path)
		swarpStr="swarp -c "+cfg["swarpcfg"]+lista+ " -IMAGEOUT_NAME "+path+"/"+self.frame+".fit "+\
		" -WEIGHTOUT_NAME  "+path+"/" +self.frame+".weight.fit "
		print "EXECUTING:\n",swarpStr
		res=commands.getoutput(swarpStr)
		print res
		return path+"/"+self.frame+".fit"

	def doOne2One(self):
		for i,fit in enumerate(self.solvefits):
			swarpStr="swarp -c "+cfg["swarpcfg"]+" "+fit+ " -IMAGEOUT_NAME "+fit 
			print "EXECUTING:\n",swarpStr
			res=commands.getoutput(swarpStr)
			print res



if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	swarp=swarp(fitsFiles)
	swarp.do()
