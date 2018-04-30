function paint() {
	var css='';
	var i=0;
	var dias=document.getElementById("dias");
	if (dias.value.length>0 && /\d+/.test(dias.value)) {
		d=Number(dias.value);
		_max=dias.options[dias.options.length-1].value;
		if (d<_max) {
			do {
				d++;
				i=document.getElementsByClassName("dia"+d).length;
			} while (i==0)
			css="div.dia"+d+", div.dia"+d+" ~ div.item {display: none;}";
		}
	}
	var webs=document.getElementsByName("web");
	for (i=0;i<webs.length;i++) {
		if (!webs[i].checked) css=css+" ."+webs[i].value+" {display: none;}"
	}
	document.getElementById("jscss").innerHTML=css;
}
document.addEventListener("DOMContentLoaded", function(event) {
    var e, dia;
    var d=[];
	var i=0;
    var now_utc = new Date();
    now_utc = now_utc - (now_utc.getTimezoneOffset()*60*1000)
	var dias=document.getElementById("dias");
    var items = document.getElementsByClassName("item");
	for (i=0;i<items.length;i++) {
        e=items[i];
        dia = Math.floor((now_utc - Number(e.getAttribute("data-time")))/8.64e7);
        e.className = e.className +" dia"+dia;
        if (dia == 0) dia = 1;
        if (dia > 0 && !d.includes(dia)) {
            dias.innerHTML = dias.innerHTML + "<option value='"+dia+"'>"+dia+"</option>";
            d.push(dia);
        }
    }
    var opts = document.getElementById("dias").options;
    opts[opts.length-1].selected = true;
	dias.addEventListener("change",function(){paint()});
	var webs=document.getElementsByName("web");
	for (i=0;i<webs.length;i++) {
		webs[i].addEventListener("change",function(){paint()});
	}
	var js=document.getElementsByClassName("js")
	for (i=0;i<js.length;i++) js[i].className=js[i].className.replace(/\bjs\b/,"");
	paint();
});
