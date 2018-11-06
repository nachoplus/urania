#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing

import commands,os, sys,glob
import simplejson
import eUdss
import eUcropper
import eUfitCrop


from PIL import Image,ImageDraw,ImageFont
import cPickle as pickle
import numpy as np
import urllib

from eUconfig import *

cfg=dict(config.items("SUPERNOVA"))

class SN_Hunter(eUcropper.cropperClass):

        def do(self,fit):
		(ra,dec)=getcenterRADEC(fit)
		self.cropGalaxies(fit,ra,dec)


        def getGalaxies(self,ra,dec):
           	#url="http://localhost:9000/hyperleda"
		url=cfg['galaxy_server']
		d = {}
		d['ra']  = ra
		d['dec'] = dec
		d['r'] = 1.5
		d['format']="pickle"
		url_values = urllib.urlencode(d)
		full_url = url + '?' + url_values
		handle= urllib.urlopen(full_url)
		galaxiesCat = pickle.load(handle)
		handle.close()
		return galaxiesCat

	def cropGalaxies(self,fits,ra,dec):
		self.loadImageFromFits(fits)
		self.loadWCSfromFits(fits)
		for galaxy in self.getGalaxies(ra,dec):
			name=galaxy['Names'].strip().split(' ')[0]
			if len(name)==0:
				name='PGC'+str(galaxy['PGC'])
			name=name.replace('+','_')
			name=name.replace('.','s')
			name=name.replace('(','')
			name=name.replace(')','')
			ra=float(galaxy['RA'])
			dec=float(galaxy['DEC'])
			minsize=60.
			r=max(float(galaxy['D'])/3600.,minsize/3600.)
			print name,ra,dec,r
			path=cfg['dir_image_base']+'/'+TodayDir()+'/'+cfg['galaxy_image']
			#path='.'
			if not os.path.exists( path):
	    			os.makedirs(path)
		        if eUfitCrop.fitCropy(fits, ra, dec, r, r, units='wcs', outfile=path+'/'+name+'.fit'):
				if self.cropRADEC(ra,dec,r,r,path+'/'+name+'.png',negative=False):
					if not self.getDSS(ra,dec,2*r*60,path+'/'+name+'.dss'):
						continue
					data=self.sex(path+'/'+name+'.fit',path+'/'+name+'.cat')
					self.paint(path+'/'+name+'.png',data,symbol=1)
					dataDSS=self.sex(path+'/'+name+'.dss.fit',path+'/'+name+'.dss.cat')
					self.paint(path+'/'+name+'.dss.png',dataDSS,symbol=2)
					candidate=False
					news=self.match(path+'/'+name)
					if len(news)>0:
						print "SUPERNOVA CANDIDATE:"+name
						self.paint(path+'/'+name+'.png',news)
						news_ = np.zeros((len(news),), dtype=[('X_IMAGE','>f4'),('Y_IMAGE','>f4')])
						for n,star in enumerate(news):
							ra_=star['ALPHA_J2000']
							dec_=star['DELTA_J2000']
							news_[n]=wcs2pix(path+'/'+name+'.dss.fit',(ra_,dec_))
						print "NEWS_:",news_
						self.paint(path+'/'+name+'.dss.png',news_,ytop=True)
						candidate=True
					self.writeJson(name,candidate)
				else:
					print "Fail to get png croppy for:",name
					continue
			else:
				print "Fail to get fit croppy for:",name
				continue

	def sex(self,fit,name):
		sexStr="sex "+fit+" -c "+cfg["sexcfg"]+" -CATALOG_NAME "+name+" -FILTER Y -FILTER_NAME "+cfg["sexfilter"]+ \
		 " -PARAMETERS_NAME "+cfg["sexparam"]+" -CHECKIMAGE_NAME "+fit+".apertures"
		print "EXECUTING:",sexStr
		res=commands.getoutput(sexStr)
		print res
		hdulist=pyfits.open(name)
		data=hdulist[1].data
		return data

	def match(self,name):
		#Search for a source in cat2 not in cat1
		seeing=4
		cat1=name+'.dss.cat'
		cat2=name+'.cat'
		stiltsStr="stilts tmatch2  fixcols=none in1="+cat1+ " in2="+cat2+" matcher=sky params="+str(seeing)+" \
	       		values1=\"ALPHA_J2000 DELTA_J2000\" \
       			values2=\"ALPHA_J2000 DELTA_J2000\" \
		   	join=2not1  \
			out="+name+".matched.cat  ofmt=fits-basic"
		print stiltsStr
		res=commands.getoutput(stiltsStr)
		print res
		hdulist=pyfits.open(name+".matched.cat")
		data=hdulist[1].data
		return data

	def getDSS(self,ra,dec,r,name):
		dss=eUdss.DSS()
		return dss.pngGet(ra,dec,r,name)

	def paint(self,name,data,symbol=0,ytop=True):
		im = Image.open(name).convert('RGB')
		h,w=im.size
		draw = ImageDraw.Draw(im)
		for star in data:
			x=int(star['X_IMAGE'])
			if ytop:
				y=h-int(star['Y_IMAGE'])
			else:
				y=int(star['Y_IMAGE'])

			if symbol==0:
				color='#ff0000'
				coords0=((x-5,y-5),(x+5,y+5))
				draw.rectangle(coords0,outline=color)
			else :
				if symbol==1:
					color='#0000ff'
				else:
					color='#00ff00'
				coords0=((x-5,y),(x+5,y))
				coords1=((x,y-5),(x,y+5))
				draw.line(coords0,width=1,fill=color)
				draw.line(coords1,width=1,fill=color)


		del draw 
		im.save(name,"PNG")

	def writeJson(self,galaxy_name,candidateFlag):
		path=cfg['dir_image_base']+'/'+TodayDir()+'/'+cfg['galaxy_image']
		filename=path+"/supernova.json"
		if not os.path.isfile(filename):
			print "NO EXISTS:",filename
		    	json_dict={}
		else:
		        fi=open(filename,"r")
			obj=fi.read()
			fi.close()
			json_dict= simplejson.loads(obj)
	
		json_dict[galaxy_name]={'candidate':candidateFlag}
		x = simplejson.dumps(json_dict)
	        fi=open(filename,"w")
		fi.write(x)
		fi.close()


if __name__ == '__main__':
	fits=sys.argv[1:][0]
	fitsFiles=sys.argv[1:]
	sn=SN_Hunter(fitsFiles)
	sn.do()






