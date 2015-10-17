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
import stat

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
webs=[]
arr=[]
bcs=[]
rk=re.compile(".*?(\\d[\\.\\d]*)\\s+km\\s+.*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
na=re.compile("\\s*Nuevo anuncio\\s*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
nb=re.compile("^\\D*(\\d+).*", re.IGNORECASE|re.MULTILINE|re.DOTALL)
sp1=re.compile("[ \t\n\r\f\v]+", re.IGNORECASE|re.MULTILINE|re.DOTALL)
sp2=re.compile("\\n[ \t\n\r\f\v]*\\n", re.IGNORECASE|re.MULTILINE|re.DOTALL)
minusculas = re.compile(".*[a-z].*")

def update(url,_price,dt):
	price=-1
	if _price.isdigit():
		price=int(_price)
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

def ya(url):
	if url in arr:
		return True
	arr.append(url)
	return False

def filtrar(_t,_d):
	t=None
	d=None
	if _t is not None and len(_t)>0:
		t=_t
	if _d is not None and len(_d)>0:
		d=_d
		if d.lower().startswith("compro "):
			return False

	if config['excluir'] is not None:
		for e in config['excluir']:
			if t is not None and e.match(t):
				return False
			if d is not None and e.match(d):
				return False
	
	if web in config:
		flt=config[web]
		if t is not None and flt[0] is not None and not flt[0].match(t):
			return False
		if d is not None and flt[1] is not None and not flt[1].match(d):
			return False

	if t is not None and d is not None and config['encontrar'] is not None:
		for e in config['encontrar']:
			if not e.match(t) and not e.match(d):
				return False

	if web not in webs:
		webs.append(web)

	return True

def dom(url):
	_dom=urlparse.urlparse(url).hostname.split(".")
	return _dom[len(_dom)-2]

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

def get(url):
	try:
		headers = {
			'Accept-Encoding': None
		}
		response = requests.get(url, headers=headers)
		soup = bs4.BeautifulSoup(response.text,"lxml")
		return soup
	except Exception, e:
		#global fd
		#fd.write("<!-- " + url + " -->")
		#fd.write("<!-- " + str(e) + " -->")
		return None

def getKm(_kms):
	kms=[rk.sub("\\1",k.get_text()) for k in _kms if rk.match(k.get_text())]
	z=len(kms)
	if z==0:
		return 9999
	km=kms[0]
	km=km.replace(".","")
	return int(km)

def getE(url,soup):
	aviso=soup.select("p.sm-md")
	if aviso is not None and len(aviso)==1:
		av=aviso[0].get_text().strip().lower()
		if av.startswith(u"hemos encontrado 0 resultados en la categoría") and av.endswith(u", por lo que también hemos buscado en todas las categorías"):
			return
	ads=[a for a in soup.select('#ListViewInner li')]
	fch=ahora - datetime.timedelta(minutes=10)
	for ad in ads:
		a=ad.select('a.vip')
		if len(a)>0:
			fch=(fch - datetime.timedelta(minutes=1))
			u="http://www.ebay.es"+urlparse.urlparse(a[0].attrs.get('href')).path
			t=a[0].get_text().strip()
			t=na.sub("",t)

			if not ya(u) and filtrar(t,None) and getKm(ad.select('ul.lvdetails li'))<50:
				d=None
				des=get(u)
				if des is not None:
					d=clean(des.select('#desc_div'))

				if filtrar(t,d):
					b=item()
					b['des']=d
					b['fuente']=url
					b['precio']=nb.sub("\\1",ad.select('li.lvprice span')[0].get_text().strip())
					b['nombre']=t
					b['url']=u
					i=ad.select('img.img')
					if len(i)>0:
						b['img']=i[0].get('src').strip()
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
		
		if not ya(u) and filtrar(t,None):
			d=None
			des=get(u)
			if des is not None:
				d=clean(des.select('p.card-product-detail-description'))
	
			if filtrar(t,d):
				b=item()
				b['fuente']=url
				b['precio']=nb.sub("\\1",ad.select('span.product-info-price')[0].get_text().strip())
				b['nombre']=t
				b['des']=d
				b['url']=u
				i=ad.select('img.card-product-image')
				if len(i)>0:
					b['img']=i[0].attrs.get('src').strip()
				b['fecha']=update(u,b['precio'],fch)
				bcs.append(b)


def getM(url,soup):
	ads=[a for a in soup.select('div.x1')]

	for ad in ads:
		a=ad.select("a.cti")[0]
		u="http://www.milanuncios.com" + a.attrs.get('href')
		t=a.get_text().strip()
		d=clean(ad.select('div.tx'))
		
		if not ya(u) and filtrar(t,d):
			b=item()
			pr=ad.select('div.pr')
			if pr is not None and len(pr)>0:
				b['precio']=nb.sub("\\1",pr[0].get_text().strip())
			b['fuente']=url
			b['nombre']=t
			b['des']=d
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
			bcs.append(b)

def getS(url,soup):
	ads=[a for a in soup.select('ul.basicList.list_ads_row')]

	for ad in ads:
		a=ad.select("a.subjectTitle")[0]
		u="http://www.segundamano.es"+urlparse.urlparse(a.attrs.get('href')).path
		t=a.get_text().strip()
		d=clean(get(u).select('#descriptionText'))

		if not ya(u) and filtrar(t,d):
			b=item()
			b['fuente']=url
			b['precio']=nb.sub("\\1",ad.select('a.subjectPrice')[0].get_text().strip())
			b['nombre']=t
			b['des']=d
			b['url']=u
			fch=fecha(ad.select("li.date a")[0].get_text().strip())
			b['fecha']=update(u,b['precio'],fch)
			i=ad.select('img.lazy')
			if len(i)>0:
				b['img']=i[0].attrs.get('title').strip()
			bcs.append(b)

def run():
	global web

	fuentes=[]
	for url in config['urls']:
		web=dom(url)
		for busca in config['buscar']:
			u=url.replace("%%s%%",busca.lower())
			soup=get(u)
			fuentes.append(u)
			if soup:
				if web=="segundamano":
					getS(u,soup)
				elif web=="milanuncios":
					getM(u,soup)
				elif web=="ebay":
					getE(u,soup)
				elif web=="wallapop":
					getW(u,soup)

	_bcs=sorted(bcs, key=lambda x: x['fecha'], reverse=True)

	_, path = tempfile.mkstemp()
	fd=codecs.open(path, "w", encoding="utf-8")
	with open('includes/head.html') as head:
		h=head.read().replace("<title></title>","<title>"+config[u'título']+"</title>")
		fd.write(h)

	d=0	
	fd.write("<div class='cuerpo'>")
	for b in _bcs:
		web=dom(b['url'])
		d=(ahora - b['fecha']).days
		fd.write("<div class='item dia"+str(d)+" "+web+"'>")
		fd.write("<h1><span class='precio'>"+b['precio']+"</span> <a href='"+b['url']+"'>"+b['nombre']+"</a></h1>")
		if b['des'] is not None:
			fd.write("<p>"+b['des']+"</p>")
		fd.write("<a class='fuente' href='"+b['fuente']+"'>Fuente: "+web+"</a>")
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
	fd.write(u"<span class='js'> Viendo los últimos <select id='dias'>")
	d=d+1
	for _i in range(1,d):
		i=str(_i)
		fd.write("<option value='"+i+"' ")
		if _i==7:
			fd.write("selected='selected'")
		fd.write(">"+i+"</option>")
	fd.write(u"</select> días en ")
	for w in webs:
		fd.write("<input type='checkbox' name='web' id='"+w+"' value='"+w+"' ")
		if w!="wallapop":
			fd.write("checked='checked'")
		fd.write("/> <label for='"+w+"'>"+w+"</label> ")
	fd.write("</span>")
	fd.write(u"<span class='c'><a href='https://github.com/santos82/bicis'>código fuente</a></span>")
	
	
	fd.write("<div class='fuente'>")
	for f in fuentes:
		fd.write("<a href='"+f+"'>"+f+"</a><br/>")
	fd.write("</div>")
	fd.write("</div>")
	
	with open('includes/foot.html') as foot:
		fd.write(foot.read())
	
	fd.close()
	shutil.copy(path, config['salida'])
	os.remove(path)
	os.chmod(config['salida'], 0644)


def getre(s):
	if isinstance(s, basestring):
		return [re.compile(s, re.IGNORECASE|re.MULTILINE|re.DOTALL)]
	r=list()
	for i in s:
		r.append(re.compile(i, re.IGNORECASE|re.MULTILINE|re.DOTALL))
	return r

def configurar(_f):
	global config
	global no
	global si
	global _wallapop

	f= file(_f, 'r')
	config = yaml.load(f)
	

	rg=['excluir','encontrar']
	
	for k in rg:
		if k in config:
			config[k]=getre(config[k])
		else:
			config[k]=None

	doms=list()
	for url in config['urls']:
		d=dom(url)
		if not d in doms:
			doms.append(d)
			if d in config:
				if isinstance(config[d], basestring):
					_re=re.compile(config[d], re.IGNORECASE|re.MULTILINE|re.DOTALL)
					config[d]=[_re,_re]
				else:
					_re1=None
					_re2=None
					if len(config[d][0])>0:
						_re1=re.compile(config[d][0], re.IGNORECASE|re.MULTILINE|re.DOTALL)
					if len(config[d])>1:
						_re2=re.compile(config[d][1], re.IGNORECASE|re.MULTILINE|re.DOTALL)
					config[d]=[_re1,_re2]
			else:
				config[d]=[None,None]

	f.close()

if __name__ == "__main__":
	ar = -1
	if len(sys.argv) <= 1 or not os.path.exists(sys.argv[1]):
		raise Exception(u'Debe pasar como argumento un fichero yaml válido')

	configurar(sys.argv[1])

	run()

