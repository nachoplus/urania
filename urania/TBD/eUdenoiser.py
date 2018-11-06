#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import pywt
import numpy as np
import pyfits

def denoise(inputFits,outputFits,sigma):
	wavelet='db4'
	with pyfits.open(inputFits) as hdulist:
		data =hdulist[0].data
		width,height = data.shape

	WC = pywt.wavedec2(data,wavelet,level=None)
	size=data.size
	print size
        threshold=float(sigma*np.sqrt(2*np.log2(size)))
	print threshold
        NWC = map(lambda x: pywt.thresholding.soft(x,threshold), WC)
	denoise_data=pywt.waverec2(NWC, wavelet)
	hdulist[0].data=denoise_data
	hdulist.writeto(outputFits,clobber=True)

