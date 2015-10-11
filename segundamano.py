# -*- coding: utf-8 -*-

import sqlite3
import datetime
import codecs
import locale
import sys

import requests
import bs4
import urlparse
import re
import yaml
import os
import tempfile
import shutil

con = sqlite3.connect("db.sqlite3", detect_types=sqlite3.PARSE_DECLTYPES)

c = con.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='AD'")
r=c.fetchone()
c.close()
if not r or len(r)==0:
	c=con.cursor()
	c.execute('''CREATE TABLE AD
		(URL TEXT PRIMARY KEY NOT NULL,
		PRICE integer NOT NULL,
		FCH timestamp NOT NULL
		)''')
	c.close()
	con.commit()


sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

ahora=datetime.datetime.now()
arr=[]
bcs=[]
rk=re.compile(".*?(\\d+)\\s+km\\s+.*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
na=re.compile("\\s*Nuevo anuncio\\s*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
nb=re.compile("^\\D*(\\d+).*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
sp1=re.compile("[ \t\n\r\f\v]+", re.IGNORECASE|re.MULTILINE|re.DOTALL)
sp2=re.compile("\\n[ \t\n\r\f\v]*\\n", re.IGNORECASE|re.MULTILINE|re.DOTALL)
minusculas = re.compile(".*[a-z].*")

def update(url,_price,dt):
	price=int(nb.sub("\\1",_price))
	c = con.cursor()
	c.execute("select FCH, PRICE from AD where URL=?",(url,))
	r=c.fetchone()
	c.close()
	if r and len(r)==2:
		if dt>=r[0] and price==r[1]:
			return r[0]
		c = con.cursor()
		c.execute("update AD set FCH=?, PRICE=? where URL=?", (dt, price, url))
		c.close()
		con.commit()
	else:
		c = con.cursor()
		c.execute("insert into AD (URL, PRICE, FCH) values (?,?,?)",(url,price,dt))
		c.close()
		con.commit()
	return dt

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

def item():
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
		global fd
		fd.write("<!-- " + url + " -->")
		fd.write("<!-- " + str(e) + " -->")
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
	fch=ahora - datetime.timedelta(minutes=10)
	for ad in ads:
		a=ad.select('a.vip')
		if len(a)>0:
			fch=(fch - datetime.timedelta(minutes=1))
			u="http://www.ebay.es"+urlparse.urlparse(a[0].attrs.get('href')).path
			t=a[0].get_text().strip()
			t=na.sub("",t)
			if not no.match(t) and not ya(u) and getKm(ad.select('ul.lvdetails li'))<50:
				b=item()
				b['fuente']=url
				b['precio']=ad.select('li.lvprice span')[0].get_text().strip()
				b['nombre']=t
				b['url']=u
				i=ad.select('img.img')
				if len(i)>0:
					b['img']=i[0].get('src').strip()
				des=get(u)
				if des is not None:
					b['des']=clean(des.select('#desc_div'))
				b['fecha']=update(u,b['precio'],fch)
				bcs.append(b)

def getW(url,soup):
	fch=ahora - datetime.timedelta(minutes=10)
	ads=[a for a in soup.select('div.card-product')]
	for ad in ads:
		fch=(fch - datetime.timedelta(minutes=1))
		a=ad.select("a.product-info-title")[0]
		u="http://es.wallapop.com"+a.attrs.get('href')
		t=a.get_text().strip()
		
		if not no.match(t) and si.match(t) and not ya(u):
			b=item()
			b['fuente']=url
			b['precio']=ad.select('span.product-info-price')[0].get_text().strip()
			b['nombre']=t
			b['url']=u
			#b['fecha']=fecha(ad.select("li.date a")[0].get_text().strip())
			i=ad.select('img.card-product-image')
			if len(i)>0:
				b['img']=i[0].attrs.get('src').strip()
			des=get(u)
			if des is not None:
				b['des']=clean(des.select('p.card-product-detail-description'))
			b['fecha']=update(u,b['precio'],fch)
			bcs.append(b)

def getM(url,soup):
	ads=[a for a in soup.select('div.x1')]

	for ad in ads:
		a=ad.select("a.cti")[0]
		u="http://www.milanuncios.com" + a.attrs.get('href')
		t=a.get_text().strip()
		if not no.match(t) and not ya(u):
			b=item()
			b['fuente']=url
			b['precio']=ad.select('div.pr')[0].get_text().strip()
			b['nombre']=t
			b['url']=u
			fch=fecha(ad.select("div.x6")[0].get_text().strip())
			b['fecha']=update(u,b['precio'],fch)
			i=ad.select('img.ee')
			if len(i)>0:
				b['img']=i[0].get('src').strip()
			else:
				_sp=get(u)
				if _sp is not None:
					sp=_sp.head.find("link", rel='image_src')
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
			b=item()
			b['fuente']=url
			b['precio']=ad.select('a.subjectPrice')[0].get_text().strip()
			b['nombre']=t
			b['url']=u
			fch=fecha(ad.select("li.date a")[0].get_text().strip())
			b['fecha']=update(u,b['precio'],fch)
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
				elif dom=="es.wallapop.com":
					getW(u,soup)

	_bcs=sorted(bcs, key=lambda x: x['fecha'], reverse=True)

	_, path = tempfile.mkstemp()
	fd=codecs.open(path, "w", encoding="utf-8")
	with open('head.html') as head:
		h=head.read().replace("<title></title>","<title>"+config[u'título']+"</title>")
		fd.write(h)

	d=0	
	fd.write("<div class='cuerpo'>")
	for b in _bcs:
		if not no.match(b['des']) and not b['des'].lower().startswith("compro "):
			_dom=urlparse.urlparse(b['url']).hostname.split(".")
			dom=_dom[len(_dom)-2]
			p=nb.sub("\\1",b['precio'])
			d=(ahora - b['fecha']).days
			fd.write("<div class='item dia"+str(d)+" "+dom+"'>")
			fd.write("<h1><span class='precio'>"+p+"</span> <a href='"+b['url']+"'>"+b['nombre']+"</a></h1>")
			fd.write("<p>"+b['des']+"</p>")
			fd.write("<a class='fuente' href='"+b['fuente']+"'>Fuente: "+dom+"</a>")
			fd.write("<div class='r'>")
			fd.write("<span class='fecha'>")
			fd.write(b['fecha'].strftime("%d/%m/%y %H:%M"))
			fd.write("</span>")
			if b['img']:
				fd.write("<img src='"+b['img']+"'/>")
			fd.write("</div>")
			fd.write("</div>")

	fd.write("</div>")
	fd.write("<div class='pie caja'>")
	fd.write(u"<span class='a'>Última actualización: " + ahora.strftime("%d/%m/%y %H:%M")+"</span>")
	fd.write(u"<span class='js dias'> Viendo los últimos <select id='dias'>")
	for _i in range(1,d):
		i=str(_i)
		fd.write("<option value='"+i+"' ")
		if _i==7:
			fd.write("selected='selected'")
		fd.write(">"+i+"</option>")
	fd.write(u"</select> días</span>")
	fd.write(u"<span class='c'><a href='https://github.com/santos82/bicis'>código fuente</a></span>")
	
	
	fd.write("<div class='fuente'>")
	for f in fuentes:
		fd.write("<a href='"+f+"'>"+f+"</a><br/>")
	fd.write("</div>")
	fd.write("</div>")
	
	with open('foot.html') as foot:
		fd.write(foot.read())
	
	fd.close()
	shutil.copy(path, config['salida'])
	os.remove(path)

if __name__ == "__main__":
	global config
	global buscar
	global no
	global si
	global urls
	global fd
	
	ar = -1
	if len(sys.argv) <= 1 or not os.path.exists(sys.argv[1]):
		raise Exception(u'Debe pasar como argumento un fichero yaml válido')
		
	f= file(sys.argv[1], 'r')
	
	config = yaml.load(f)

	buscar=config['buscar']
	no=re.compile(config['excluir'], re.IGNORECASE|re.MULTILINE|re.DOTALL)
	si=re.compile(config['exigir'], re.IGNORECASE|re.MULTILINE|re.DOTALL)
	urls=config['urls']

	run()

