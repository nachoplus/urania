#!/usr/bin/python
# -*- coding: iso-8859-15 -*-


"""
======
Cutout
======
Heavily base on:
https://code.google.com/p/agpy/source/browse/trunk/agpy/cutout.py

Generate a cutout image from a .fits file
"""

import sys
import pyfits
import wcsutil
import numpy


def fitCropy(filename, xc, yc, xw=25, yw=25, units='pixels', outfile=None,
        clobber=True, verbose=False):
    """
    Inputs:
        file  - .fits filename or pyfits HDUList (must be 2D)
        xc,yc - x and y coordinates in the fits files' coordinate system (CTYPE)
        xw,yw - x and y width (pixels or wcs)
        units - specify units to use: either pixels or wcs
        outfile - optional output file
    """

    if isinstance(filename,str):
        file = pyfits.open(filename)
        opened=True
    elif isinstance(filename,pyfits.HDUList):
        file = filename
        opened=False
    else:
        raise Exception("cutout: Input file is wrong type (string or HDUList are acceptable).")

    head = file[0].header.copy()

    if head['NAXIS'] > 2:
        raise DimensionError("Too many (%i) dimensions!" % head['NAXIS'])
    cd1 = head.get('CDELT1') if head.get('CDELT1') else head.get('CD1_1')
    cd2 = head.get('CDELT2') if head.get('CDELT2') else head.get('CD2_2')
    if cd1 is None or cd2 is None:
        raise Exception("Missing CD or CDELT keywords in header")
    wcs = wcsutil.WCS(head)


    if units=='pixels':
	    xx,yy = xc,yc
            xmin,xmax = numpy.max([0,xx-xw]),numpy.min([head['NAXIS1'],xx+xw])
            ymin,ymax = numpy.max([0,yy-yw]),numpy.min([head['NAXIS2'],yy+yw])
    elif units=='wcs':
	    xx,yy = wcs.sky2image(xc,yc)
	    xw=xw/numpy.abs(cd1)	
	    yw=yw/numpy.abs(cd2)
            xmin,xmax = numpy.max([0,xx-xw]),numpy.min([head['NAXIS1'],xx+xw])
            ymin,ymax = numpy.max([0,yy-yw]),numpy.min([head['NAXIS2'],yy+yw])
    else:
            raise Exception("Can't use units %s." % units)

    print xc,yc
    print xw,yw
    print xx,yy
    print xmin,xmax
    print ymin,ymax

    if xmax < 0 or ymax < 0:
            print ValueError("Max Coordinate is outside of map: %f,%f." % (xmax,ymax))
	    return False
    if ymin >= head.get('NAXIS2') or xmin >= head.get('NAXIS1'):
            print  ValueError("Min Coordinate is outside of map: %f,%f." % (xmin,ymin))
	    return False	

    head['CRPIX1']-=xmin
    head['CRPIX2']-=ymin
    head['NAXIS1']=int(xmax-xmin)
    head['NAXIS2']=int(ymax-ymin)

    if head.get('NAXIS1') == 0 or head.get('NAXIS2') == 0:
            print  ValueError("Map has a 0 dimension: %i,%i." % (head.get('NAXIS1'),head.get('NAXIS2')))
	    return False	

    img = file[0].data[ymin:ymax,xmin:xmax]
    newfile = pyfits.PrimaryHDU(data=img,header=head)
    if verbose: print "Cut image %s with dims %s to %s.  xrange: %f:%f, yrange: %f:%f" % (filename, \
		file[0].data.shape,img.shape,xmin,xmax,ymin,ymax)

    if isinstance(outfile,str):
        newfile.writeto(outfile,clobber=clobber)

    if opened:
        file.close()

    return True
    #return newfile

if __name__ == '__main__':
	f=sys.argv[1:][0]
	fitCropy(f, 1000, 1000, xw=250, yw=250, units='pixels').writeto('kk_pix.fit')
	fitCropy(f,1.63538421677,12.8697202788 , xw=0.250, yw=0.250, units='wcs').writeto('kk_wcs.fit')
