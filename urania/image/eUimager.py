#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing
#Make a png copy of FITs image
#Input:Fit(s) fits files to copy
#Nacho Mas Diciembre 2013

import commands,os, sys,glob
import eUcatalog
from PIL import Image,ImageDraw,ImageFont
import f2n
import copy

from eUconfig import *

cfg=dict(config.items("IMAGER"))



class imagerClass(helper):

	def fitsPNGs(self):
		bining=int(cfg['rebin'])
		self.png_dest=map(lambda x:cfg["dir_image_base"]+"/"+self.getToday()+"/"+cfg["dir_image_png"]+"/"+os.path.basename(x),self.pngs)
		for i,fits in enumerate(self.solvefits):
			print "Generating PNG from:",fits
			myimage = f2n.fromfits(fits)
			myimage.setzscale("auto")
			myimage.rebin(bining,method="max")
			# z2 = "ex" means extrema -> maximum in this case.
			myimage.makepilimage("log", negative = False)
			# We can choose to make a negative image.
			#myimage.writeinfo([fits,"DATE:"+self.dates[i]+" EXP="+str(self.exposures[i]),"TELE:"+self.telescopes[i]], colour=(255,100,0))
			dir_dest=os.path.dirname(self.png_dest[i])
			if not os.path.exists( dir_dest):
	    				os.makedirs(dir_dest)
			myimage.tonet(self.png_dest[i])

	def aperturesPNGs(self):
		bining=int(cfg['rebin'])
		self.apertures_dest=map(lambda x:cfg["dir_image_base"]+"/"+self.getToday()+"/"+cfg["dir_image_apertures"]+"/"+os.path.basename(x),self.pngsApertures)
		for i,fits in enumerate(self.aperturesfiles):
			print "Generating PNG from:",fits
			try:
				myimage = f2n.fromfits(fits)
			except:
				return
			myimage.setzscale( z1=50,z2="auto")
			myimage.rebin(bining,method="max")
			#z2 = "ex" means extrema -> maximum in this case.
			myimage.makepilimage("log", negative = True)
			# We can choose to make a negative image.
			#myimage.writetitle(fits, colour=(200, 0, 0))
			#myimage.writeinfo([fits,"DATE:"+self.dates[i]+" EXP="+str(self.exposures[i]),"TELE:"+self.telescopes[i]], colour=(255,100,0))
			dir_dest=os.path.dirname(self.apertures_dest[i])
			if not os.path.exists( dir_dest):
	    				os.makedirs(dir_dest)
			#myimage.pilimage=myimage.pilimage.convert("L")
			myimage.tonet(self.apertures_dest[i])

	def paintNGCs(self):
		bining=int(cfg['rebin'])
		print "PAINT GALAXIES"
		mpc_mask_dir=cfg['base_html_dir']+"/"+self.getToday()+"/ngc_mask"
		if not os.path.exists(mpc_mask_dir):
		    os.makedirs(mpc_mask_dir)
		cat=eUcatalog.Cat()
		print "load hyperleda"
	 	cat.loadFIT(cfg['ngc_cat'])
		print "load hyperleda:done"
		(minRA,minDEC,maxRA,maxDEC)=self.maxBox()
		cat.data=filter(lambda x:(minRA<float(x['ALPHA_J2000'])<maxRA) and (minDEC<float(x['DELTA_J2000'])<maxDEC),cat.data)
		print cat.data
		if len(cat.data)==0:
			return
		for i,solvefit in enumerate(sorted(self.solvefits)):

			im_mask = Image.new("RGBA", (self.frameWidths[i]/bining, self.frameHeights[i]/bining))
			draw_mask = ImageDraw.Draw(im_mask)

			for k,mpc in enumerate(cat.data):
				coords=(self.wcs2pix(solvefit,(float(mpc['ALPHA_J2000']),float(mpc['DELTA_J2000']))))
				#print coords
				if coords==(0,0):
					continue
				#print i,k,mpc['Name'],mpc['ALPHA_J2000'],mpc['DELTA_J2000']
				(x0,y0)=map(lambda x:int(x),coords)
				x=x0/bining
				y=(self.frameHeights[i]-y0)/bining
				color=cfg['ngc_color']
				#r=float(mpc['MAG'])
				#r=int(cfg['ngc_radius'])
				r=float(mpc['D'])*bining/self.arcsecperpix
				print (x,y,r)
				##CROP GALAXIES
				"""
				if x>0 and x<self.frameWidths[i] and y>0 and y<self.frameHeights[i]:
					(xmin,xmax,ymin,ymax)=((x-r)*bining,(x+r)*bining,self.frameHeights[i]-(y+r)*bining,self.frameHeights[i]-(y-r)*bining)
					self.crop(solvefit,"test%03i-%02i.png" % (k,i),(xmin,xmax,ymin,ymax))
					print xmin,xmax,ymin,ymax
				"""
				draw_mask.rectangle((x-r, y-r, x+r, y+r),outline=color)
				draw_mask.text((x+r,y+r),"PA:"+str(mpc['PA'])+"MAG:"+str(mpc['logD25']),fill=color)
				#draw_mask.text((x+r,y+r),mpc['Name']+mpc['Object'],fill=color)


			del draw_mask
			im_mask.save(mpc_mask_dir+"/"+self.pngs[i],"PNG")

   	def paintMPCs(self):
		bining=int(cfg['rebin'])
		mpc_mask_dir=cfg['base_html_dir']+"/"+self.getToday()+"/mpc_mask"
		if not os.path.exists(mpc_mask_dir):
		    os.makedirs(mpc_mask_dir)

		for i,mpc_cat in enumerate(self.mpc_filtered):
			cat=eUcatalog.Cat()
		 	cat.loadFIT(mpc_cat)
			im_mask = Image.new("RGBA", (self.frameWidths[i]/bining, self.frameHeights[i]/bining))
			draw_mask = ImageDraw.Draw(im_mask)

			for k,mpc in enumerate(cat.data):
				print i,k,mpc['KEY'],mpc['RA'],mpc['DEC']		
				(x0,y0)=map(lambda x:int(x),(self.wcs2pix(self.solvefits[i],(float(mpc['RA']),float(mpc['DEC'])))))
				x=x0/bining
				y=(self.frameHeights[i]-y0)/bining
				print (x,y)
				try:
					if mpc['PRECOVERY']==1:
						color='#ff00ff'
					else:
						color=cfg['mpc_color']
						

				except:
					color='#fff000'
				#r=float(mpc['MAG'])
				r=int(cfg['mpc_radius'])
				draw_mask.rectangle((x-r,  y-r, x+r, y+r),outline=color)
				draw_mask.text((x+r,y+r),str(int(mpc['MAG']*10)/10),fill=color)


			del draw_mask
			im_mask.save(mpc_mask_dir+"/"+self.pngs[i],"PNG")

   	def paintDetections(self,what):
		
		bining=int(cfg['rebin'])
		if what=="fastmover":
			catalog="G"+self.Fmovers
			dir_postfix="fastmover_mask"
			color=cfg['fastmover_color']
			r=int(cfg['fastmover_radius'])
			shape=1 #rectangle
		if what=="asteroid":
			catalog=self.Amovers
			dir_postfix="asteroid_mask"
			color=cfg['asteroid_color']
			r=int(cfg['asteroid_radius'])
			shape=2 #circle


		mask_dir=cfg['base_html_dir']+"/"+self.getToday()+"/"+dir_postfix
		if not os.path.exists(mask_dir):
		    os.makedirs(mask_dir)

		cat=eUcatalog.Cat()
		try:
			print "PAINT DETECTIONS FROM:",catalog
	 		cat.loadFIT(catalog)
		except:
			print "painting:no detections"
			return

		for i,dummy in enumerate(self.pngs):
			im_mask = Image.new("RGBA", (self.frameWidths[i]/bining, self.frameHeights[i]/bining))
			draw_mask = ImageDraw.Draw(im_mask)
			in_frame=filter(lambda x:x['FRAME']==i+1,cat.data)
			if shape==2:
				im_reg_file=open(mask_dir+"/"+self.pngs[i]+".region",'w')
				im_reg_file.write("<map name='"+self.pngs[i]+".region'  id='"+self.pngs[i]+".region'>\n")

			for k,mpc in enumerate(in_frame):
				print i,k,mpc['ID'],mpc['ALPHA_J2000'],mpc['DELTA_J2000']		
				(x0,y0)=map(lambda x:int(x),(self.wcs2pix(self.solvefits[i],(float(mpc['ALPHA_J2000']),float(mpc['DELTA_J2000'])))))
				x=x0/bining
				y=(self.frameHeights[i]-y0)/bining
				print (x,y)
				if shape==1:
					draw_mask.rectangle((x-r, y-r, x+r, y+r),outline=color)
					draw_mask.text((x+r,y+r),str(mpc['ID']),fill=color)
				if shape==2:
					draw_mask.ellipse((x-r, y-r, x+r, y+r),outline=color)
					draw_mask.text((x+r+1,y-2*r-1),str(mpc['ID']),fill=color)
					#MAKE IMAGE REGIONS
					#string="<area class='asteroid_link' title='"+mpc['ID']+"' shape='circle' coords='"+str(x)+","+str(y)+","+str(r)+"' href='"+self.getToday()+"/slow_animations/animate-"+str(mpc['ID'])+".gif'/>\n"
					string="<area class='asteroid_link' title='"+mpc['ID']+ \
					"' shape='circle' coords='"+str(x)+","+str(y)+","+str(r*1.2)+ \
					"' href='slow.html?date="+self.getToday()+"&frame="+self.frame+"&asteroid="+mpc['ID']+"'/>\n"
					im_reg_file.write(string)

			del draw_mask
			im_mask.save(mask_dir+"/"+self.pngs[i],"PNG")
			if shape==2:
				im_reg_file.write("</map>")
				im_reg_file.close()



	def writeRegistra(self):
		bining=float(cfg['rebin'])
		fi=open(os.path.dirname(self.png_dest[0])+"/"+self.frame+".registra",'w')
		for i,fits in enumerate(self.solvefits):
			#(xx,yy)=map(lambda x:int(x),(self.wcs2pix(self.solvefits[0],(self.centers[i]))))
			(xx,yy)=self.wcs2pix(self.solvefits[0],(self.centers[i]))			
			x=xx
			y=(self.frameHeights[i]-yy)
			(x0,y0)=map(lambda x:float(x),(self.frameWidths[i]/2, self.frameHeights[i]/2))
			Xb=(x-x0)/bining
			Yb=(y-y0)/bining
			print "registra displacement",i,"(x,y):",Xb,Yb,"INT (x,y):%.0f %0.f" % (Xb,Yb)
			line="%u %.0f %.0f\n" % (i,Xb,Yb)
			fi.write(line)
		fi.close()

	def do(self):
		self.fitsPNGs()
		self.aperturesPNGs()		
	  	return True

   	def paintSats(self):
		rebin=int(cfg["rebin"])
		sat_frame=[]
		htmldir=cfg["base_html_dir"]+"/"+self.getToday()+"/sats"
		if not os.path.exists(htmldir):
		    os.makedirs(htmldir)
		subdirs=["withsats_mask","matched_mask","withsats","matched","/apertures/withsats/","/apertures/matched/"]
		for dir in subdirs:
			if not os.path.exists(htmldir+"/"+dir):
			    os.makedirs(htmldir+"/"+dir)

		for i,sat_cat in enumerate(self.sat_filtered):
			cat=eUcatalog.Cat()
			try:
			 	cat.loadFIT(sat_cat)
			except:
				continue
			im_mask = Image.new("RGBA", (self.frameWidths[i]/rebin, self.frameHeights[i]/rebin))
			draw_mask = ImageDraw.Draw(im_mask)
			#im = Image.open(self.png_dest[i])
			#draw = ImageDraw.Draw(im)
			sat_list=[]
			for k,sat in enumerate(cat.data):
				sat_list.append(sat['KEY'])
				print i,k,sat['NAME'],sat['RA'],sat['DEC']		
				(x0,y0)=map(lambda x:int(x),(self.wcs2pix(self.solvefits[i],(float(sat['RA']),float(sat['DEC'])))))
				x=x0/rebin
				y=(self.frameHeights[i]-y0)/rebin
				print (x,y)
				"""
				draw.line(((x-5,y),(x+5,y)),width=1,fill='#00ff00')
				draw.line(((x,y-5),(x,y+5)),width=1,fill='#00ff00')
				draw.text((x,y),sat['NAME'],fill='#f0fff0')
				draw.text((x,y+12),sat['KEY'],fill='#f0fff0')
				draw.text((x,y+24),str(int(sat['ELEVATION']/1000))+" km",fill='#f0fff0')
				"""
				sat_color='#00ff00'
				draw_mask.line(((x-5,y),(x+5,y)),width=1,fill=sat_color)
				draw_mask.line(((x,y-5),(x,y+5)),width=1,fill=sat_color)
				draw_mask.text((x,y),sat['NAME'],fill=sat_color)
				draw_mask.text((x,y+12),sat['KEY'],fill=sat_color)
				draw_mask.text((x,y+24),str(int(sat['ELEVATION']/1000))+" km",fill=sat_color)
			sat_frame.append(sat_list)
			#del draw 
			del draw_mask
			self.setStats('satellites'+str(i),sat_list)
			self.setStats('sat_number'+str(i),len(sat_list))
			if len(sat_list)!=0:
				im_mask.save(htmldir+"/withsats_mask/"+self.pngs[i],"PNG")
				"""
				im.save(htmldir+"/withsats/"+self.pngs[i],"PNG")
				filename=self.apertures_dest[i]
				if os.path.isfile(htmldir+"/apertures/withsats/"+os.path.basename(filename)):
					os.remove(htmldir+"/apertures/withsats/"+os.path.basename(filename))
				os.symlink(filename,htmldir+"/apertures/withsats/"+os.path.basename(filename))
				"""

		sat_match=[]
		for i in xrange(len(self.sat_filtered)-1):
			print i
			matched=[]
			for k in sat_frame[i]:
				print "Sat n inside frame:",k,i
				if k in sat_frame[i+1]:
					matched.append(k)
					sat_match.append(matched)
		self.setStats('sat_match',sat_match)		
		self.setStats('sat_match_number',len(sat_match))
	
		if len(sat_match)!=0:
			"""
			for png in self.apertures_dest:
				filename=os.path.basename(png)
				if os.path.isfile(htmldir+"/apertures/matched/"+filename):
					os.remove(htmldir+"/apertures/matched/"+filename)
			TypeError: ufunc 'rint' output (typecode 'f') could not be coerced to provided output parameter (typecode 'B') according to the casting rule ''same_kind''	os.symlink(png,htmldir+"/apertures/matched/"+filename)
			"""
			for png in self.pngs:
				filename=os.path.basename(png)
				if os.path.isfile(htmldir+"/matched/"+filename):
					os.remove(htmldir+"/matched/"+filename)
				if os.path.isfile(htmldir+"/withsats/"+filename):
					os.symlink(htmldir+"/withsats/"+filename,htmldir+"/matched/"+filename)
	
				if os.path.isfile(htmldir+"/matched_mask/"+filename):
					os.remove(htmldir+"/matched_mask/"+filename)
				if os.path.isfile(htmldir+"/withsats_mask/"+filename):
					os.symlink(htmldir+"/withsats_mask/"+filename,htmldir+"/matched_mask/"+filename)
			return len(sat_match)
		return 0

if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	imager=imagerClass(fitsFiles)
	imager.paintNGCs()
	#imager.paintDetections("asteroid")
	#imager.paintDetections("fastmover")
	#imager.paintMPCs()
	imager.fitsPNGs()
	imager.writeRegistra()
