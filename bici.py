# -*- coding: utf-8 -*-

import datetime
import codecs
import locale
import sys

import requests
import bs4
import urlparse
import re

sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

ahora=datetime.datetime.now()
buscar=['trekking', 'cicloturismo', 'urbana', 'paseo']
arr=[]
bcs=[]
no=re.compile(u".*(tamaño plegada|un solo piñ[oó]n|fixie|PLEGABLE|Motoreta|piñ[oó]n fijo|niñ[oa]|Bicicleta est[aá]tica|single speed|única velocidad).*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
rk=re.compile(".*?(\\d+)\\s+km\\s+.*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
na=re.compile("\\s*Nuevo anuncio\\s*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
nb=re.compile("^\\D*(\\d+).*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
sp1=re.compile("[ \t\n\r\f\v]+", re.IGNORECASE|re.MULTILINE|re.DOTALL)
sp2=re.compile("\\n[ \t\n\r\f\v]*\\n", re.IGNORECASE|re.MULTILINE|re.DOTALL)
minusculas = re.compile(".*[a-z].*")

urls=['http://www.segundamano.es/bicicletas-paseo-de-segunda-mano-madrid-particulares/%%s%%.htm?ca=28_s&sort_by=1&od=1&ps=100&pe=400', 'http://www.milanuncios.com/bicicletas-paseo-ciudad-de-segunda-mano-en-madrid/%%s%%.htm?desde=100&hasta=400&demanda=n&vendedor=part&cerca=s', 'http://www.ebay.es/sch/Bicicletas-/177831/i.html?_udlo=100&_sadis=50&_fspt=1&_udhi=400&_mPrRngCbx=1&_stpos=28005&_from=R40&_nkw=bicicleta%20%%s%%&LH_PrefLoc=99&_dcat=177831&rt=nc&LH_ItemCondition=3000&_trksid=p2045573.m1684']

def fecha(dt):
	if dt.startswith("hoy "):
		return ahora.replace(hour=int(dt[4:6]),minute=int(dt[7:9]))
	if dt.startswith("ayer "):
		return (ahora.replace(hour=int(dt[5:7]),minute=int(dt[8:10])) - datetime.timedelta(days=1))
	sp=dt.split()
	mes=1
	if sp[1]=="seg":
		return ahora - datetime.timedelta(seconds=int(sp[0]))
	if sp[1]=="min":
		return ahora - datetime.timedelta(minutes=int(sp[0]))
	if sp[1]=="hora" or sp[1]=="horas":
		return ahora - datetime.timedelta(hours=int(sp[0]))
	if sp[1]=="dia" or sp[1]=="dias" or unicode(sp[1])==u"día" or unicode(sp[1])==u"días":
		return ahora - datetime.timedelta(days=int(sp[0]))
	if sp[1]=="ene":
		mes=1
	elif sp[1]=="feb":
		mes=2
	elif sp[1]=="mar":
		mes=3
	elif sp[1]=="abr":
		mes=4
	elif sp[1]=="may":
		mes=5
	elif sp[1]=="jun":
		mes=6
	elif sp[1]=="jul":
		mes=7
	elif sp[1]=="ago":
		mes=8
	elif sp[1]=="sep":
		mes=9
	elif sp[1]=="oct":
		mes=10
	elif sp[1]=="nov":
		mes=11
	elif sp[1]=="dic":
		mes=12
	else:
		return None
	return ahora.replace(day=int(sp[0]),hour=int(sp[2][0:2]),minute=int(sp[2][3:5]),month=mes)

def clean(_s):
	if len(_s)==0:
		return ''
	s=_s[0].get_text()
	s=sp1.sub(" ",s)
	s=sp2.sub("\\n",s)
	if not minusculas.match(s):
		s=s.lower()
	return s.strip()

def bici():
	b={}
	b['url']=''
	b['nombre']=''
	b['precio']=''
	b['des']=''
	b['img']=''
	b['fecha']=None
	return b
	

def ya(url):
	if url in arr:
		return 1
	arr.append(url)
	return 0

def get(url):
	try:
		headers = {
			'Accept-Encoding': None
		}
		response = requests.get(url, headers=headers)
		soup = bs4.BeautifulSoup(response.text,"lxml")
		return soup
	except Exception, e:
		print "<!-- " + url + " -->"
		print "<!-- " + str(e) + " -->"
		return None

def getKm(_kms):
	kms=[rk.sub("\\1",k.get_text()) for k in _kms if rk.match(k.get_text())]
	z=len(kms)
	if z==0:
		return 9999
	km=kms[0]
	return int(km)

def getE(url,soup):
	ads=[a for a in soup.select('#ListViewInner li')]

	for ad in ads:
		a=ad.select('a.vip')
		if len(a)>0:
			u="http://www.ebay.es"+urlparse.urlparse(a[0].attrs.get('href')).path
			t=a[0].get_text().strip()
			t=na.sub("",t)
			if not no.match(t) and not ya(u) and getKm(ad.select('ul.lvdetails li'))<50:
				b=bici()
				b['fuente']=url
				b['precio']=ad.select('li.lvprice span')[0].get_text().strip()
				b['nombre']=t
				b['url']=u
				i=ad.select('img.img')
				if len(i)>0:
					b['img']=i[0].get('src').strip()
				b['des']=clean(get(u).select('#desc_div'))
				bcs.append(b)


def getM(url,soup):
	ads=[a for a in soup.select('div.x1')]

	for ad in ads:
		a=ad.select("a.cti")[0]
		u="http://www.milanuncios.com" + a.attrs.get('href')
		t=a.get_text().strip()
		if not no.match(t) and not ya(u):
			b=bici()
			b['fuente']=url
			b['precio']=ad.select('div.pr')[0].get_text().strip()
			b['nombre']=t
			b['url']=u
			b['fecha']=fecha(ad.select("div.x6")[0].get_text().strip())
			i=ad.select('img.ee')
			if len(i)>0:
				b['img']=i[0].get('src').strip()
			else:
				sp=get(u).head.find("link", rel='image_src')
				if sp is not None:
					b['img']=sp['href']
			b['des']=clean(ad.select('div.tx'))
			bcs.append(b)

def getS(url,soup):
	ads=[a for a in soup.select('ul.basicList.list_ads_row')]

	for ad in ads:
		a=ad.select("a.subjectTitle")[0]
		u="http://www.segundamano.es"+urlparse.urlparse(a.attrs.get('href')).path
		t=a.get_text().strip()

		if not no.match(t) and not ya(u):
			b=bici()
			b['fuente']=url
			b['precio']=ad.select('a.subjectPrice')[0].get_text().strip()
			b['nombre']=t
			b['url']=u
			b['fecha']=fecha(ad.select("li.date a")[0].get_text().strip())
			i=ad.select('img.lazy')
			if len(i)>0:
				b['img']=i[0].attrs.get('title').strip()
			b['des']=clean(get(u).select('#descriptionText'))
			bcs.append(b)

def run():

	fuentes=[]
	for url in urls:
		dom=urlparse.urlparse(url).hostname
		for busca in buscar:
			u=url.replace("%%s%%",busca)
			soup=get(u)
			fuentes.append(u)
			if soup:
				if dom=="www.segundamano.es":
					getS(u,soup)
				elif dom=="www.milanuncios.com":
					getM(u,soup)
				elif dom=="www.ebay.es":
					getE(u,soup)

	mindate = datetime.datetime(datetime.MINYEAR, 1, 1)
	def ordenar(x):
	  return x['fecha'] or mindate

	_bcs=sorted(bcs, key=ordenar, reverse=True)
	
	print "<div class='cuerpo'>"
	for b in _bcs:
		if not no.match(b['des']) and not b['des'].lower().startswith("compro "):
			p=nb.sub("\\1",b['precio'])
			print "<div class='bici",
			if b['fecha'] is not None and (ahora - b['fecha']).days>30:
				print " old",
			print "'>"
			print "<h1><span class='precio'>"+p+"</span> <a href='"+b['url']+"'>"+b['nombre']+"</a></h1>"
			print "<p>"+b['des']+"</p>"
			print "<a class='fuente' href='"+b['fuente']+"'>Fuente</a>"
			print "<div class='r'>"
			if b['fecha']:
				print "<span class='fecha'>"
				print b['fecha'].strftime("%d/%m/%y %H:%M")
				print "</span>"
			if b['img']:
				print "<img src='"+b['img']+"'/>"
			print "</div>"
			print "</div>"

	print "</div>"
	print "<div class='pie'>"
	print u"<span class='a'>Última actualización: " + ahora.strftime("%d/%m/%y %H:%M")+"</span>"
	print u"<span class='c'><a href='https://github.com/santos82/bicis'>código en github.com</a></span>"
	
	
	print "<div class='fuente'>"
	for f in fuentes:
		print "<a href='"+f+"'>"+f+"</a><br/>"
	print "</div>"
	print "</div>"
	
if __name__ == '__main__':
	run()

