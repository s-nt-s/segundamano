function fire(i,e) {
	if ("createEvent" in document) {
		var evt = document.createEvent("HTMLEvents");
		evt.initEvent(e, false, true);
		i.dispatchEvent(evt);
	}
	else
		i.fireEvent("on"+e);
}

function setDias(d) {
	var aux=0;
	do {
		d++;
		aux=document.getElementsByClassName("dia"+d).length;
	} while (aux==0)
	document.getElementById("jscss").innerHTML="div.dia"+d+", div.dia"+d+" ~ div.item {display: none;}";
}
document.addEventListener("DOMContentLoaded", function(event) {
	var dias=document.getElementById("dias");
	dias.addEventListener("change",function(){
		if (this.value.length>0 && /\d+/.test(this.value)) setDias(Number(this.value))
	});
	fire(dias,"change");
	var js=document.getElementsByClassName("js")
	var i;
	for (i=0;i<js.length;i++) js[i].className=js[i].className.replace(/\bjs\b/,"");
});
