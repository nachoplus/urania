#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import pyfits
import numpy as np

class fitMaths():

	def __init__(self, fitsname):
		self.hdulist = pyfits.open(fitsname)
		self.fitsname=fitsname

	def __add__(self, other):
		new=fitMaths(self.fitsname)
		other=other.hdulist[0].data
		new.hdulist[0].data = new.hdulist[0].data + other
		return new

	def __sub__(self, other):
		new=fitMaths(self.fitsname)
		other=other.hdulist[0].data
		new.hdulist[0].data = new.hdulist[0].data - other
		return new

	def __div__(self, other):
		new=fitMaths(self.fitsname)
		other=other.hdulist[0].data
		new.hdulist[0].data = new.hdulist[0].data / other
		return new


	def __mul__(self, other):
		new=fitMaths(self.fitsname)
		other=other.hdulist[0].data
		new.hdulist[0].data = new.hdulist[0].data * other
		return new


	def __rmul__(self, scalar):
		new=fitMaths(self.fitsname)
		new.hdulist[0].data = scalar * new.hdulist[0].data 
		return new


	def dark(self, darkfitsname):
		dark = pyfits.open(darkfitsname)
		darkExp= float(dark[0].header['EXPTIME'])

		new=fitMaths(self.fitsname)
		newExp= float(new.hdulist[0].header['EXPTIME'])

		factor=newExp/darkExp
		print newExp,darkExp,factor
		other=dark[0].data
		new.hdulist[0].data = new.hdulist[0].data - factor * other
		return new

	def flat(self, flatfitsname):
		flat = pyfits.open(flatfitsname)
		flatExp= float(flat[0].header['EXPTIME'])

		new=fitMaths(self.fitsname)
		newExp= float(new.hdulist[0].header['EXPTIME'])

		other=flat[0].data
		factor=np.median(other)
		print newExp,flatExp,factor
		new.hdulist[0].data = new.hdulist[0].data /  (other /factor)
		return new

	def save(self,f):
		self.hdulist.writeto(f,clobber=True) 

if __name__ == '__main__':
    '''
	Test
    '''
    f_light1=fitMaths('001558+114848-scan005-01.fit')
    f_dark=fitMaths('darkmedian2.fit')
    f_flat=fitMaths('flatmedian2.fit')
    r=(1/3)*f_light1
    r=f_light1/f_flat
    #dark_sustracted=f_light1.dark('darkmedian2.fit')
    #dark_sustracted.save('newimage.fits')
    flat_sustracted=f_light1.flat('flatmedian2.fit')
    flat_sustracted.save('newimage.fits')
