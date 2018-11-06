#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing

import commands,os, sys,glob

from PIL import Image,ImageDraw,ImageFont
import f2n
import copy
import numpy as np
import wcsutil
import pyfits


class cropperClass:


	def loadWCSfromFits(self,fits):
		self.wcsFits=fits


	def loadImageFromFits(self,fits):
		self.fitsToCrop = f2n.fromfits(fits)


	def cropRADEC(self,ra,dec,deltaRA,deltaDEC,fichero,negative=True):
		print "Generating crop from:",self.wcsFits, "RA,DEC,deltas coords:",ra,dec,deltaRA,deltaDEC
		wcs = wcsutil.WCS(pyfits.open(self.wcsFits)[0].header)
		ramin=ra-deltaRA
		ramax=ra+deltaRA
		decmin=dec-deltaDEC
		decmax=dec+deltaDEC
		print ramin,ramax
		print decmin,decmax
		(x0,y0) = wcs.sky2image(ramax,decmin)
		(x1,y1) = wcs.sky2image(ramin,decmax)
		print (x0,y0)
		print (x1,y1)
		return self.cropXY(x0,x1,y0,y1,fichero,negative)


	def cropXY(self,x0,x1,y0,y1,fichero,negative=True):
		#Always return a image padded with black if outside limits
		#Check limits
		print "Generating crop from:",self.fitsToCrop, "x,y coords:",x0,x1,y0,y1
		x0,x1,y0,y1=map(lambda x:int(x),(x0,x1,y0,y1))
		xx0,xx1,yy0,yy1=x0,x1,y0,y1
		overflow=False
		x0offset=0
		x1offset=int(x1-x0)
		y0offset=0
		y1offset=int(y1-y0)
		if x0<0:
			if x1<0:
				return False
			xx0=0
			overflow=True
			x0offset=int(-x0)

		if x1>self.fitsToCrop.origwidth:
			if x0>self.fitsToCrop.origwidth:
				return False			
			xx1=self.fitsToCrop.origwidth
			overflow=True
			x1offset=int(xx1-xx0)

		if y0<0:
			if y1<0:
				return False
			yy0=0
			overflow=True
			y1offset=int(yy1-yy0)


		if y1>self.fitsToCrop.origheight:
			if y0>self.fitsToCrop.origheight:
				return False
			yy1=self.fitsToCrop.origheight
			overflow=True
			y0offset=int(y1-yy1)


		if abs(xx0-xx1)<=10 or abs(yy0-yy1)<=10:
			print "Not enough size. "
			return False

		myimage = copy.deepcopy(self.fitsToCrop)
		print (xx0,xx1,yy0,yy1)
		myimage.crop(xx0,xx1,yy0,yy1)
		myimage.setzscale(z1="auto",z2="flat",samplesizelimit=10000,nsig=3)
		#myimage.setzscale(z1="auto",z2="auto",samplesizelimit=10000,nsig=3)
		#myimage.setzscale(-1000,5000)
		# z2 = "ex" means extrema -> maximum in this case.
		if negative:
			myimage.makepilimage("log", negative = True)
		else:
			myimage.makepilimage("lin")
		# We can choose to make a negative image.


		if not overflow:
		#if True:	
			myimage.tonet(fichero)
		else:
			print "f2n overflow, Padding in black"
			box=(x0offset,y0offset,x1offset,y1offset)
			print "BOX",box
			w,h = int(x1-x0),int(y1-y0)
			print "W/H",w,h
			data = np.empty( (w,h), dtype=np.uint8)
			data.fill(25)
			img = Image.fromarray(data)
			im  = myimage.pilimage		
			print "SIZE:",img.size,im.size
			img.paste(im, box)
			img.save(fichero,"PNG")

	  	return True	


	def test(self):
		print "Generating PNG from:",fits
		myimage = copy.deepcopy(self.fitsToCrop)
		myimage.crop(70, 270, 60, 260)
		myimage.setzscale("auto")
		# z2 = "ex" means extrema -> maximum in this case.
		myimage.makepilimage("log", negative = True)
		# We can choose to make a negative image.
		myimage.tonet("test.png")

	def test0(self):
		self.cropXY(70, 270, 60, 260,'test1.png')
		self.cropXY(-70, 130, 60, 260,'test2.png')
		self.cropXY(70, 270, -60, 140,'test3.png')
		self.cropXY(3056-200, 3056, 3056-200, 3056,'test4.png')
		self.cropXY(3056-100, 3156, 3056-200, 3056,'test5.png')
		self.cropXY(3056-200, 3056, 3056-100, 3156,'test6.png')
		#self.cropXY(70, 270, -60, 200,'test3.png')
		#self.cropXY(70, 270, 3000, 4000,'test4.png')


def writeGif(AnimateGif, imgs, duration=0.4):
	use_convert=True
	if use_convert:
		#animategif library do not work properly
		#use ImageMagick instead
		cmd="convert -delay "+str(duration*100)+" -loop 0 "
		for im in imgs:
			cmd=cmd+im+" "
		cmd=cmd+AnimateGif
		res=commands.getoutput(cmd)
		print res
	else:
		from images2gif import writeGif
		imgsI = [Image.open(fn) for fn in imgs]
		writeGif(AnimateGif, imgsI, duration)

if __name__ == '__main__':
	fits=sys.argv[1:][0]
	cropper=cropperClass()
	cropper.loadImageFromFits(fits)
	cropper.test0()	





