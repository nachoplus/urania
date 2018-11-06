#!/usr/bin/python
#-*- coding: iso-8859-15 -*-
#NACHO MAS
import ephem,urllib


def group(lst, n):
  for i in range(0, len(lst), n):
    val = lst[i:i+n]
    if len(val) == n:
      yield tuple(val)


#Code to get TLE and Comet (format Xephem) from Minor Planet Center

class internetCatalogue:

	def comet(self,name='',commet=1):
		if commet==1:
			url="http://www.minorplanetcenter.org/iau/Ephemerides/Comets/Soft03Cmt.txt"
	        else:
			url="http://www.minorplanetcenter.net/iau/Ephemerides/Unusual/Soft03Unusual.txt"
		f=urllib.urlopen(url)
		s=f.read().split('\n')
		#Elimino texto sobrante
		s=filter(lambda x:x!='' and x[0]!='#',s)
		#busco una entrada concreta
		CometID=name
		comet=filter(lambda x:x.find(CometID)!=-1, s)
		print comet[0]
		return ephem.readdb(comet[0])

	def neo(self,name=''):

		f=urllib.urlopen(url)
		s=f.read().split('\n')
		#Elimino texto sobrante
		s=filter(lambda x:x!='' and x[0]!='#',s)
		#busco una entrada concreta
		NeoID=name
		Neo=filter(lambda x:x.find(NeoID)!=-1, s)
		print Neo[0]
		return ephem.readdb(Neo[0])




	#TLE from http://celestrak.com/NORAD/elements/
	def readTLE(self,url):
		url=url
		f=urllib.urlopen(url)
		data=f.read().split('\r\n')
		s=group(data,3)
		return s

	def readTLEfromfile(self,url):
		f=open(url)
		data=f.read().split('\n')
		#print data
		s=group(data,3)
		return s

	def TLE(self,url,name):
		data=self.readTLE(url)
		element=filter(lambda x:x[0].find(name)!=-1, data)
		element=element[0]
		print element
		return ephem.readtle(element[0],element[1],element[2])
		

	def ISS(self):	
	#ISS http://celestrak.com/NORAD/elements/stations.txt
		url="http://celestrak.com/NORAD/elements/stations.txt"
		return self.TLE(url,'ISS')



	def iridium(self,n):
		#Iridium http://celestrak.com/NORAD/elements/iridium.txt
		url="http://celestrak.com/NORAD/elements/iridium.txt"
		return self.TLE(url,'IRIDIUM '+ str(n))

	def geo(self,name):	
	#GEOSTATIONARY http://celestrak.com/NORAD/elements/geo.txt
		url="http://celestrak.com/NORAD/elements/geo.txt"
		return self.TLE(url,name)

#Los 100 mas brillantes
#http://celestrak.com/NORAD/elements/visual.txt



	def allIridium(self):
		url="http://celestrak.com/NORAD/elements/iridium.txt"
		iri=[]
		s=self.readTLE(url)
		for element in s:
			if element[0].split('[')[1][0]=='+':
				iri.append(ephem.readtle(element[0],element[1],element[2]))
		return iri
		
	def allTLE(self,url,fromfile=False):
		TLEs=[]
		self.TLE_IOs=[]
		if fromfile:	
			s=self.readTLEfromfile(url)
		else:
			s=self.readTLE(url)
		
		for i,element in enumerate(s):
			#print element
			#Catch malformed TLEs
			try:	
				TLEs.append(ephem.readtle(element[0],element[1],element[2]))
				self.TLE_IOs.append((element[0],element[1],element[2]))
			except:
				print "Malformed TLE:",element
		return TLEs

if __name__=='__main__':
	
	observer=ephem.city('Madrid')
	observer.date=ephem.Date('2011/10/23 20:00')
	i=internetCatalogue()
	geo=i.geo('HISPASAT')
	geo.compute(observer)
	print geo.ra,geo.dec




