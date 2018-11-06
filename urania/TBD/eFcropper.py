#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#Prepare html an images to show the result
#Input:'Gmovers_'{framename}.cat
#Output:figs and html code
#config file parameters:
#
#	Section: [FCROPPIES]
#		html_base_dir
#		croppy_size
#		animation_margin
#
#Nacho Mas Junio 2013
#Status: work. Further housekeeping needed

from  matplotlib import pyplot

import pyfits
#from pylab import *
import commands,os, sys
import shutil
import csv
import re
import numpy as np
import eUcatalog
import eUcropper
from PIL import Image,ImageDraw,ImageMath
import glob


from eUconfig import *

cfg=dict(config.items("FCROPPIES"))



def Debug(string):
	debug=cfg["debug"]
	if debug in ['True','true','yes','y']:
		print string

class cropClass(eUcatalog.moverCat,helper):
	tam=int(cfg["croppy_size"])
	margen=int(cfg["animation_margin"])

	def do(self):

		if not os.path.isfile(self.Fmovers):
			print "NO EXISTS:",self.Fmovers
		    	return 1
		else:
			print "Processing movers in:",self.Fmovers		
		  	self.loadFIT("G"+self.Fmovers)

		self.htmldir=cfg["html_base_dir"]+"/"+self.getToday()+"/"+self.frame
		if not os.path.exists(self.htmldir):
			    os.makedirs(self.htmldir)
		self.AnimationDir=self.htmldir+"/animations"
		self.ImagesDir=self.htmldir+"/images"
		self.CroppiesDir=self.htmldir+"/croppies"
		self.CorrelationDir=self.htmldir+"/correlation"	
		self.images()
		self.animation()
		self.correlations()
		self.croppies()
		self.html()
		self.clean()

	def clean(self):
		pass

	def cropper(self,SrcFrame,x0,y0,x1,y1,DstFrame,negative=False):
		crp=eUcropper.cropperClass()
		crp.loadImageFromFits(SrcFrame)
		return crp.cropXY(x0,x1,y0,y1,DstFrame,negative)

	def animation(self):
		AnimationDir=self.AnimationDir
		if not os.path.exists(AnimationDir):
	 		os.makedirs(AnimationDir)
		res=commands.getoutput("rm "+AnimationDir+"/anima*" )
		margen=0
		movers=self.data
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

			print "RA/DECmax:",RAmax,DECmax
			#maxCoord=("%s %s" % (RAmax,DECmax),"%s %s" % (RAmin,DECmin))
			margen=int(float(mover['A_WORLD'].max())*3600*8)
			print "ANIMATION MARGEN:",mover['A_WORLD'],mover['A_WORLD'].max()*3600,margen
			if margen>self.frameWidth/8:
				margen=self.frameWidth/8
			for i,id in enumerate(mover['frame']):
				print "Processing frame:",id
				SrcFrame="./"+self.solvefits[int(id)-1]
				RA=RAs[i]
				DEC=DECs[i]
				
				(x0,y0)=map(lambda x:int(x),(self.wcs2pix(SrcFrame,(RAmax,DECmax))))
				x0=x0-margen
				y0=y0+margen
				(x1,y1)=map(lambda x:int(x),(self.wcs2pix(SrcFrame,(RAmin,DECmin))))
				x1=x1+margen
				y1=y1-margen
				(x,y)=map(lambda x:int(x),(self.wcs2pix(SrcFrame,(RA,DEC))))				
				x=x-x0
				y=y0-y
				

				deltaX=abs(x1-x0)/2
				deltaY=abs(y1-y0)/2

				print x,y

				ymean=(y0+y1)/2
				xmean=(x0+x1)/2
				print "ANI:",x,y,x0,y0,x1,y1,deltaX,deltaY
				tam=max(deltaX,deltaY)
				AnimationGif=AnimationDir+"/animation%s-%02u.png" % (moverID,int(id))
				if os.path.isfile(AnimationGif):
					os.remove(AnimationGif)

				if not self.cropper(SrcFrame,xmean-deltaX,ymean-deltaY,xmean+deltaX,ymean+deltaY,AnimationGif):
					continue
			
	
				im = Image.open(AnimationGif).convert('RGB')
				draw = ImageDraw.Draw(im)
				draw.line(((x-5,y),(x+5,y)),width=1,fill='#ff0000')
				draw.line(((x,y-5),(x,y+5)),width=1,fill='#ff0000')
				del draw 
				im.save(AnimationGif,"PNG")
		
				img=Image.open(AnimationGif)
				factor=1.
				maxAnimationSize=float(cfg["max_animation_size"])
				if deltaX>maxAnimationSize: 
					factor=(maxAnimationSize/deltaX)
				if deltaY>maxAnimationSize:
					factor=(maxAnimationSize/deltaY)
				print factor,deltaX,deltaY
				img1=img.resize((int(deltaX*factor),int(deltaY*factor)),Image.ANTIALIAS)
				#img1.show()
				img1.save(AnimationGif)


			file_names = sorted((fn for fn in os.listdir(AnimationDir) if fn.startswith('animation%s-' %moverID)))
			imgs = [AnimationDir+"/"+fn for fn in file_names]
			if len(file_names)>0:
				print file_names
				#AnimateGif=AnimationDir+"/animate-%02u.gif" % moverID
				AnimateGif=AnimationDir+"/animate-%s.gif" % moverID
				eUcropper.writeGif(AnimateGif, imgs, duration=0.4)

				



	def correlations(self):
		CorrelationDir=self.CorrelationDir
		if not os.path.exists(CorrelationDir):
			    os.makedirs(CorrelationDir)
		movers=self.data
		moversIDs=set(movers['ID'])
		margen=5
		for moverID in moversIDs:
			print "Correlation mover ID:",moverID
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			W0=float(mover['W[0]'][0])
			W1=float(mover['W[1]'][1])
			RAs=-mover['ALPHA_J2000']
			DECs=mover['DELTA_J2000']
			DISTANCEs=mover['LINE_DIS']


			#upper rigth corner
			x0=min(RAs)*3600-margen
			y0=min(DECs)*3600-margen
			#lower left corner
			x1=max(RAs)*3600+margen
			y1=max(DECs)*3600+margen
			deltaX=x1-x0
			deltaY=y1-y0
			if deltaX>deltaY:
				ymean=(y0+y1)/2
				y0=ymean-deltaX/2
				y1=ymean+deltaX/2
			else:
				xmean=(x0+x1)/2
				x0=xmean-deltaY/2
				x1=xmean+deltaY/2
			# plotting the line
			line = (W0*(-RAs)+W1)*3600 # regression line
			pyplot.figure(figsize=(6,4), dpi=80)
			pyplot.plot(RAs*3600,line,'r-',RAs*3600,DECs*3600,'o')
			#print axis()
			#print (x0,x1,y0,y1)
			pyplot.axis((x0,x1,y0,y1))
			GOOD_DETECTION=mover['GOODFLAG'][0]
			for i,mover_frame in enumerate(mover['frame']):
				print "Processing frame:",i
				ra=RAs[i]
				dec=DECs[i]
				dis=DISTANCEs[i]
				pyplot.annotate("GOOD_FLAG:"+str(GOOD_DETECTION),xy=(ra*3600,dec*3600), xycoords='data', textcoords='offset points')
				pyplot.annotate(str(int(dis*100)/100.),xy=(ra*3600,dec*3600), xycoords='data', \
			        xytext=(+18, +18), textcoords='offset points', fontsize=10, \
			        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))

			pyplot.savefig(CorrelationDir+"/correlation"+str(moverID)+".png")	
			pyplot.close()				

   			

	def croppies(self):
		CroppiesDir=self.CroppiesDir
		if not os.path.exists(CroppiesDir):
		    os.makedirs(CroppiesDir)
		tam=0
		movers=self.data
		moversIDs=set(movers['ID'])
		print moversIDs
		for moverID in moversIDs:
			print "Croping mover ID:",moverID
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			tam=int(float(mover['A_WORLD'].max()*3600*4))
			framelist=[]
			for k in range(3):
				for kk in range(3):
					dummy=CroppiesDir+"/croppy%s-%02u-%02u.png" % (moverID,k+1,kk+1)
					res=commands.getoutput("cp "+configpath+"/nodata.png "+dummy)

			for id in mover['frame']:

				print "Processing frame:",id
				SrcFrame=self.solvefits[int(id)-1]
				moverFlt=(mover['frame']==id)
				mov=mover[moverFlt]
				
				print mov

				ra_org=float(mov['ALPHA_J2000'][0])
				dec_org=float(mov['DELTA_J2000'][0])

				for idd in mover['frame']:
					print "Processing subframe:",moverID,"-",id,"-",idd

					DstFrame=self.solvefits[int(idd)-1]
					print "Dest Frame:",DstFrame
					(x1,y1)=map(lambda x:int(x),(self.wcs2pix(DstFrame,(ra_org,dec_org))))	
					print x1,y1
					CropFrame=CroppiesDir+"/croppy%s-%02u-%02u.png" % (moverID,int(id),int(idd))
					res=commands.getoutput("cp "+configpath+"/nodata.png "+CropFrame)
					if not self.cropper(DstFrame,x1-tam,y1-tam,x1+tam,y1+tam,CropFrame,negative=True):
						continue
					if id==idd:
						framelist.append(CropFrame)

			outname=self.ImagesDir+"/image"+str(moverID)+".png"
			self.compose_image(framelist,outname)

			
	def images(self):
		ImagesDir=self.ImagesDir
		if not os.path.exists(ImagesDir):
		    os.makedirs(ImagesDir)
		res=commands.getoutput("cp "+configpath+"/nodata.png "+self.ImagesDir+"/.")
		movers=self.data
		moversIDs=set(movers['ID'])
		for moverID in moversIDs:
			#res=commands.getoutput("rm image"+str(moverID)+"*.fits" )
			print "Imaging mover ID:",moverID
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			Ndetections=len(mover)
			print mover['A_WORLD'].max()
			tam=int(float(mover['A_WORLD'].max()*3600*4))
			if tam>self.frameWidth/10:
				tam=self.frameWidth/10

			if tam <50:
				tam=50

			framelist=[]
			for id in mover['frame']:
				print "Processing frame:",id
				#SrcFrame=frame+"-%02u.fit" % int(id)
				#print "imagen SrcFrame:",SrcFrame
				SrcFrame="./"+self.aperturesfiles[int(id)-1]
				print "imagen SrcFrame:",SrcFrame
				moverFlt=(mover['frame']==id)
				mov=mover[moverFlt]
				x=int(float(mov['X_IMAGE']))
				y=int(float(mov['Y_IMAGE']))
				ra_sat=float(mov['RA_SAT'])
				dec_sat=float(mov['DEC_SAT'])
				(x_sat,y_sat)=self.wcs2pix(SrcFrame,(ra_sat,dec_sat))	
				print "SAT:",(ra_sat,dec_sat),(x_sat,y_sat)
				x_sat=x_sat-x+tam
				y_sat=y-y_sat+tam			
				print "SAT(cropped):",(x_sat,y_sat)

				speed=float(mov['SPEED'])
				PA=float(mov['PA_ASTROMETRICA']) 

				#xspeed=speed*np.cos(np.pi/2-PA*np.pi/180)*self.exposure/(self.arcsecperpix*60)
				#yspeed=speed*np.sin(np.pi/2-PA*np.pi/180)*self.exposure/(self.arcsecperpix*60)

				xspeed=speed*np.cos(PA*np.pi/180)*self.exposure/(self.arcsecperpix*60)
				yspeed=speed*np.sin(PA*np.pi/180)*self.exposure/(self.arcsecperpix*60)
				
				sep=8
				x0line=tam-xspeed/2-tam/sep
				y0line=tam-yspeed/2-tam/sep
				x1line=tam+xspeed/2-tam/sep
				y1line=tam+yspeed/2-tam/sep



				print "X/YSPEED:",xspeed,yspeed,speed
				print (x0line,y0line),(x1line,y1line)

				DstFrame=ImagesDir+"/image%s-%02u.png" % (moverID,int(id))
				if os.path.isfile(DstFrame):
					os.remove(DstFrame)

				if not self.cropper(SrcFrame,x-tam,y-tam,x+tam,y+tam,DstFrame):
					continue

				framelist.append(DstFrame)
				xx=tam
				yy=tam
				linewidth=int(tam/50)
				linewidth=1
				im = Image.open(DstFrame).convert('RGB')
				draw = ImageDraw.Draw(im)
				#draw.line(((xx-5,yy),(xx+5,yy)),width=1,fill='#ff0000')
				draw.line(((x_sat-tam/10,y_sat),(x_sat+tam/10,y_sat)),width=linewidth/2,fill='#0000ff')
				draw.line(((x_sat,y_sat-tam/10),(x_sat,y_sat+tam/10)),width=linewidth/2,fill='#0000ff')
				draw.line(((x0line,y0line),(x1line,y1line)),width=linewidth,fill='#ff0000')
				#draw.line(((xx,yy-10),(xx,yy+10)),width=linewidth/2,fill='#ff0000')
				#draw.line(((xx-10,yy),(xx+10,yy)),width=linewidth/1,fill='#ff0000')
				#draw.ellipse(((xx-tam/5,yy-tam/5),(xx+tam/5,yy+tam/5)),outline='#ff0000')
				del draw 
				im.save(DstFrame)

			#outname=ImagesDir+"/image"+str(moverID)+".png"
			#self.compose_image(framelist,outname)


	def compose_image(self,framelist,outname):
		imlist={}
		cmd="("
		for i,fr in enumerate(framelist):
			imlist['i'+str(i)]=Image.open(fr)
			if i==0:
				cmd=cmd+"float(i"+str(i)+")"
			else:			
				cmd=cmd+"+float(i"+str(i)+")"
		cmd=cmd+")/"+str(len(framelist))
		print cmd
		print imlist

		out = ImageMath.eval(cmd, imlist).convert('P')
		out.save(outname,"PNG")


	def html(self):

		self.html_table()
		res=commands.getoutput("cp "+configpath+"/Feetf.css "+self.htmldir+"/.")

		with open(self.htmldir+"/"+self.frame+".html_inc", 'r') as content_file:
		    content = content_file.read()
		print "Generando HTML",self.frame+".html"
		f=open(self.htmldir+"/"+self.frame+".html","w")
		f.write("<html><head>")
		f.write("</head><body>\n")
		f.write('<link rel="stylesheet" type="text/css" href="./Feetf.css" />\n')
		f.write(content)
		f.write("</body></html>")
		f.close()
		res=commands.getoutput("ln -s "+self.htmldir+"/"+self.frame+".html "+self.htmldir+"/index.html")

	def formatVector(self,vector,mul):
		Str="["
		for v in vector:
			valor=v*mul
			Str=Str+ "%4.1f " % valor
		return Str+"]"

	def html_table(self):
		ImagesDir=self.ImagesDir.replace(self.htmldir,'.')
		AnimationDir=self.AnimationDir.replace(self.htmldir,'.')
		CroppiesDir=self.CroppiesDir.replace(self.htmldir,'.')
		CorrelationDir=self.CorrelationDir.replace(self.htmldir,'.')
		f=open(self.htmldir+"/"+self.frame+".html_inc","w")
		movers=self.data
		moversIDs=set(movers['ID'])
		for moverID in moversIDs:
			f.write("<table class='fastmover'>\n")
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			DESIGNATION=mover['ID'][0]
			f.write("<tr >\n")
			f.write("<td >")
		 	mpcorb=self.writeMPC(self.htmldir+"/"+self.frame+"-"+ "%s" % moverID+'.mpcorb',ID=moverID)
			print mpcorb
			HeadStr= \
				"<table class='moverinfo'>" +\
				"<tr>" +\
				"<td label='ID'>"+DESIGNATION+"</td>" +\
				"<td colspan=2 label='MPCOBS'>"+"<a href='./"+self.frame+"-"+ "%s" % moverID+".mpcorb'>FILE</a><br>"+str(mpcorb)+"</td>" +\
				"<td label='TRAILNESS'>"+self.formatVector(mover['TRAILNESS'],1)+"</td>" +\
				"<td colspan=2 label='IMAGE'><a href='../../blinker.html?date="+self.getToday()+"&frame="+self.frame+"'>BLINKER</a></td>" +\
				"</tr>" +\
				"<tr>" +\
				"<td colspan=2 label='FRAME'>"+self.frame+ "</td>" +\
				"<td label='DATE'>"+mover['DATETIME'][0] + "</td>" +\
				"<td label='MAG'>"+self.formatVector(mover['MAG_AUTO'],1) + "</td>" +\
				"<td label='SPEED'>" + \
					"<a href='../../propagator.html?date="+str(mover['MJDATE'][0])+"&speed="+ \
					str(mover['MEANSpeed'][0])+"&pa="+str(mover['PA0_ASTROMETRICA'][0])+ \
                                        "&id="+DESIGNATION + \
					"&ra="+str(mover['ALPHA_J2000'][0]) + "&dec="+str(mover['DELTA_J2000'][0])+"'>" + \
					self.formatVector(mover['SPEED'],1) + \
					"</a>" +\
				"</td>" +\
				"</tr>" +\
				"<tr>" +\
				"<td label='PA'>"+str(int(mover['PA0_ASTROMETRICA'][0])) +"</td>" +\
				"<td label='PA-ELIP'>"+self.formatVector(mover['THETA_J2000'],1) + "</td>" +\
				"<td label='A_WORLD'>"+self.formatVector(mover['A_WORLD'],3600) + "</td>" +\
				"<td label='ELONG'>"+self.formatVector(mover['ELONGATION'],1) + "</td>" +\
				"<td label='RMS'>"+"%g " % mover['CORRELATION'][0] + "</td>" +\
				"</tr>" +\
				"</table>"

			f.write(HeadStr)

			f.write("</td>\n")
			f.write("</tr>\n")


			f.write("<tr >\n")
			f.write("<td >")
			f.write("<table class='moverimage'>\n")
			f.write("<tr>\n")
			if len(mover['frame'])==2 and mover['frame'][-1]==3:
				f.write("<td>\n")
				f.write('\n<a href=../images/png/'+self.pngs[0]+'><img src=\"'+ImagesDir+'/nodata.png\"  /></a>\n')
				f.write("</td>\n")

			for id in mover['frame']:
				moverFlt=(mover['frame']==id)
				mov=mover[moverFlt]
				f.write("<td>\n")
				f.write('\n<a href=../images/png/'+self.pngs[int(id)-1]+'><img src=\"'+ImagesDir+'/image%s-%02u.png' % (moverID,int(id)) +'\"  /></a>\n')
				f.write("</td>\n")

			if len(mover['frame'])==2 and mover['frame'][-1]==2:
				f.write("<td>\n")
				f.write('\n<a href=../images/png/'+self.pngs[2]+'><img src=\"'+ImagesDir+'/nodata.png\"  /></a>\n')
				f.write("</td>\n")


			f.write("<td>\n")
			f.write('\n<img src=\"'+ImagesDir+'/image'+str(moverID)+'.png"   />\n')
			f.write("</td>\n")
			f.write("<td>\n")
			#croppies imagen table
			f.write("<table class='cropiesimage'>")
			for row in range(3):
				f.write("<tr>")
				for col in range(3):
					f.write("<td>")
					CropFrame=CroppiesDir+"/croppy%s-%02u-%02u.png" % (moverID,int(row)+1,int(col)+1)
					f.write('\n<img src=\"'+CropFrame+'"   />\n')
					f.write("</td>")
				f.write("</tr>")
			f.write("</table>")
			#f.write('\n<img src=\"'+CroppiesDir+'/croppies'+str(moverID)+'.gif"   />\n')
			f.write("</td>\n")
			f.write("</tr>\n")

			f.write("</table>\n")

			f.write("<tr>\n")
			f.write("<td>\n")
			f.write("<table class='satdata'>\n")
			f.write("<tr>\n")
			if (len(mover['frame'])==2 and mover['frame'][-1]==3) :
				f.write("<td>\n" )
				f.write("<table class='satinfo'>\n")
				f.write("<td  label='SAT'>[nan]</td>\n" )
				f.write("</table>\n")		
				f.write("</td>\n" )
			for id in mover['frame']:
				moverFlt=(mover['frame']==id)
				mov=mover[moverFlt]
				if np.isnan(mov['ELEVATION_SAT']):
					f.write("<td>\n" )
					f.write("<table class='satinfo'>\n")
					f.write("<td  label='SAT'>[NOT FOUND]</td>\n" )
					f.write("</table>\n")		
					f.write("</td>\n" )
					continue
				f.write("<td>\n" )
				f.write("<table class='satinfo'>\n")		
				f.write("<tr>\n" )		
				f.write("<td label='KEY'>"+mov['KEY_SAT']+"</td>\n" )
				f.write("</tr>\n" )
				f.write("<tr>\n" )		
				f.write("<td label='NAME'>"+mov['NAME_SAT']+"</td>\n" )
				f.write("</tr>\n" )		
				f.write("<tr>\n" )		
				f.write("<td label='O-C'> "+str(mov['DIS_SAT'])+"</td>\n" )
				f.write("</tr>\n" )		
				f.write("<tr>\n" )		
				f.write("<td label='ELEV:'>"+str(int(mov['ELEVATION_SAT']/1000))+" km</td>\n" )
				f.write("</tr>\n" )
				f.write("</table>\n")		
				f.write("</td>\n" )		
			if (len(mover['frame'])==2 and mover['frame'][-1]==2) :
				f.write("<td>\n" )
				f.write("<table class='satinfo'>\n")
				f.write("<td  label='SAT'>[nan]</td>\n" )
				f.write("</table>\n")		
				f.write("</td>\n" )
			f.write("<td></td>\n" )
			f.write("<td></td>\n" )
			f.write("</tr>\n")
			f.write("</table>\n")
			f.write("<table class='animation'>\n")
			f.write("<tr  >\n")
			f.write("<td id='animation'>\n")
			f.write('\n<img src=\"'+AnimationDir+'/animate-'+'%s' % moverID+'.gif"  />\n')
			f.write("</td>\n")
			f.write("<td >\n")
			f.write('\n<img src=\"'+CorrelationDir+'/correlation'+str(moverID)+'.png"  width=250 height=200 border="1" />\n')
			f.write("</td>\n")
			f.write("</tr>\n")
			f.write("</table>\n")

			f.write("</tr>\n")
			f.write("</table>\n")
		f.close()


if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	cropp=cropClass(fitsFiles)
	cropp.do()






