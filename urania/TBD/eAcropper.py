#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing

import commands,os, sys,glob
import simplejson
import eUcatalog
import eUcropper
from PIL import Image,ImageDraw,ImageFont
import math
from eUconfig import *

cfg=dict(config.items("ACROPPIES"))

class cropClass(eUcatalog.moverCat,eUcropper.cropperClass,helper):

	def loadCat(self):
		self.loadFIT(self.Amovers)

	def animations(self):
	  AnimationDir=cfg["base_html_dir"]+"/"+self.getToday()+"/slow_animations"
	  margen=15
	  movers=self.data
	  print movers
	  moversIDs=set(movers['ID'])

	  for moverID in moversIDs:
		print "Animation mover ID:",moverID
		moverFlt=(movers['ID']==moverID)
		mover=movers[moverFlt]
		RAmax=max(mover['ALPHA_J2000'])
		DECmax=max(mover['DELTA_J2000'])
		RAmin=min(mover['ALPHA_J2000'])
		DECmin=min(mover['DELTA_J2000'])

		RAs=mover['ALPHA_J2000']
		DECs=mover['DELTA_J2000']

		RA=RAs[1]
		DEC=DECs[1]

		SrcFrame=self.solvefits[1]
		(x0,y0)=map(lambda x:int(x),(self.wcs2pix(SrcFrame,(RAmax,DECmax))))
		x0=x0-margen
		y0=y0+margen
		(x1,y1)=map(lambda x:int(x),(self.wcs2pix(SrcFrame,(RAmin,DECmin))))
		x1=x1+margen
		y1=y1-margen
		deltaX=abs(x1-x0)/2
		deltaY=abs(y1-y0)/2
		delta=max(deltaX,deltaY)
		print "DELTA:",delta,delta*2
		for id,dummy in enumerate(self.solvefits):
		  	SrcFrame=self.solvefits[id]
		  	self.loadImageFromFits(SrcFrame)
		  	self.loadWCSfromFits(SrcFrame)

		  	print "Processing frame:",id

			(x,y)=map(lambda x:int(x),(self.wcs2pix(SrcFrame,(RA,DEC))))				


			DstFrame=AnimationDir+"/animation%s-%02u.png" % (moverID,int(id))
			#DstFrame=AnimationDir+"/animation%s-%02u.gif" % (moverID,int(id))
			if os.path.isfile(DstFrame):
				os.remove(DstFrame)

			if not os.path.exists(AnimationDir):
		 		os.makedirs(AnimationDir)
			#print "DELTAS",delta,x-delta,x+delta,y-delta,y+delta
			if not self.cropXY(x-delta,x+delta,y-delta,y+delta,DstFrame):
				continue
					
			#PUT DE MARKS
			if 0:
				print "Reference marks"
				im = Image.open(DstFrame).convert('RGB')
				draw = ImageDraw.Draw(im)
				draw.line(((x-5,y),(x+5,y)),width=1,fill='#000000')
				draw.line(((x,y-5),(x,y+5)),width=1,fill='#000000')
				draw.line(((0,0),(15,15)),width=1,fill='#000000')
				print (x-delta/10,y-delta/10),(x+delta/10,y+delta/10)
				draw.ellipse(((delta/10,delta/10),(delta-delta/10,delta-delta/10)),outline='#ff0000')
				del draw 
				im.save(DstFrame,"PNG")
				

		file_names = sorted((fn for fn in os.listdir(AnimationDir) if fn.startswith('animation%s-' %moverID)))
		if len(file_names)>0:
			imgs = [AnimationDir+"/"+fn for fn in file_names]
			AnimateGif=AnimationDir+"/animate-%s.gif" % moverID
			eUcropper.writeGif(AnimateGif, imgs, duration=0.4)	

	def writeJson(self):
		AnimationDir=cfg["base_html_dir"]+"/"+self.getToday()+"/slow_animations"
		filename=AnimationDir+"/"+self.frame+".json"
		movers=self.data
		moversIDs=set(movers['ID'])
		json_dict={'FRAME':self.frame,'SLOWMOVERS':[]}
		json_dict_reduce={}
	  	for moverID in moversIDs:
			print "JSON mover ID:",moverID
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			m=mover[0]
			if not math.isnan(round(m['DIS_MPC'],0)):
				oc=round(m['DIS_MPC'],0)
			else:
				oc="-"
			mpcobs=self.writeMPC('/dev/null',ID=moverID)
			#r="%4.3e" % m['CORRELATION']
			r="%4.3e" % m['RMS']
			entry= {'ID':moverID,'MAG':round(m['MEAN_MAG'],1),'SPEED':round(m['MEANspeed'],1),'PA':round(m['PA'],1), \
				'KNOW':bool(m['KNOW']),'OC':oc,'R':r,'MPCOBS':mpcobs}
			entryReduce= {moverID:{'MAG':round(m['MEAN_MAG'],1),'SPD':round(m['MEANspeed'],1),'PA':round(m['PA'],1),'KNW':bool(m['KNOW']),'OC':oc,'R':r}}
			#print moverID,entry
			json_dict['SLOWMOVERS'].append(entry)
			json_dict_reduce.update(entryReduce)
		x = simplejson.dumps(json_dict)
	        fi=open(filename,"w")
		fi.write(x)
		fi.close()	
		print json_dict_reduce
		return 	json_dict_reduce


if __name__ == '__main__':
	fits=sys.argv[1:][0]
	fitsFiles=sys.argv[1:]
	cropp=cropClass(fitsFiles)
	cropp.loadCat()
	#cropp.loadFIT("N"+cropp.Amovers)	
	cropp.animations()
	#cropp.writeJson()






