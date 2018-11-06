#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Utility
#Retrive DSS images or URLs

import urllib
import commands,os,sys
from PIL import Image,ImageDraw,ImageFont
import f2n


#DSS M13
#"http://archive.eso.org/dss/dss/image?ra=16%2041%2041.634000&dec=+36%2027%2040.74984&x=10.000000&y=10.000000&mime-type=download-gif&Sky-Survey=DSS2-infrared&equinox=J2000&statsmode=VO"

#DSS M27
#http://stdatu.stsci.edu/cgi-bin/dss_search?v=poss2ukstu_ir&r=19+59+36.38&d=%2B22+43+15.7&e=J2000&h=15.0&w=15.0&f=gif&c=none&fov=NONE&v3=

class DSS():

	def ESOgetURL(self,ra,dec,size):
		#Get the url to retrive 
		#p.e. m13=dss.getURL('16 41 41.634000','+36 27 40.74984',50)
		url="http://archive.eso.org/dss/dss/image"
		d = {}
		d['ra'] = ra
		d['dec'] = dec
		d['x'] = str(size)
		d['y'] = str(size)
		d['mime-type']="download-fits"
		#d['sky-Survey']="DSS2-infrared"
		d['sky-Survey']="DSS"
		d['equinox']="J2000"
		d['statsmode']="VO"
		print d
		url_values = urllib.urlencode(d)
		full_url = url + '?' + url_values
		return full_url
		
		#data = urllib.request.urlopen(full_url)

	def getURL(self,ra,dec,size):
		#Get the url to retrive 
		#p.e. m13=dss.getURL('16 41 41.634000','+36 27 40.74984',50)
		size=size
		url="http://stdatu.stsci.edu/cgi-bin/dss_search"
		d = {}
		d['r'] = ra
		d['d'] = dec
		d['v'] = 'poss2ukstu_ir'
		d['e'] = 'J2000'
		d['h'] = str(size)
		d['w'] = str(size)
		d['f']="gif"
		d['c']="none"
		d['v3']=""
		print d
		url_values = urllib.urlencode(d)
		full_url = url + '?' + url_values
		return full_url


	def cds_sesame(self,obj):
		#Get the coords of and obj using sesame
		print obj
		res=commands.getoutput('sesame -ol '+obj)
		res=res.split('\n')
		for r in res:
			rr=r.split()
			try:
				if rr[0]=='%J':					
					return float(rr[1]),float(rr[2])
			except:
				pass

	def pngGet(self,ra,dec,size,name=""):
	  try:
		if name=="":
			name=str(ra)+"_"+str(dec)+"_x"+str(size)
		url=self.ESOgetURL(ra,dec,size)
		print url
		urllib.urlretrieve(url,name+'.fit')
		myimage= f2n.fromfits(name+'.fit')
		#myimage.setzscale("auto")
		myimage.setzscale(z1="auto",z2="flat",samplesizelimit=10000,nsig=3)
		# z2 = "ex" means extrema -> maximum in this case.
		myimage.makepilimage("lin", negative = False)
		# We can choose to make a negative image.
		myimage.tonet(name+".png")
		return True
	  except:
		print "FAIL to get DSS image"
		return False

	def pngSesame(self,obj):
		ra,dec=self.cds_sesame(obj)		
		self.pngGet(ra,dec,20,obj)

	def getMessier(self):
	#Donwload all Messier catalog
  	    for i in xrange(1,109):
		obj="M%u" %i
		pngSesame(obj)


if __name__ == '__main__':
	obj=sys.argv[1:][0]
	size=30
	dss=DSS()
	ra,dec=dss.cds_sesame(obj)
	print dss.getURL(ra,dec,size)
	dss.pngGet(ra,dec,size)
