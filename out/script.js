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
	var dias=document.getElementById("dias");
	dias.addEventListener("change",function(){
		if (this.value.length>0 && /\d+/.test(this.value)) paint()
	});
	var i=0;
	var webs=document.getElementsByName("web");
	for (i=0;i<webs.length;i++) {
		webs[i].addEventListener("change",function(){paint()});
	}
	var js=document.getElementsByClassName("js")
	var i;
	for (i=0;i<js.length;i++) js[i].className=js[i].className.replace(/\bjs\b/,"");
	paint();
});
