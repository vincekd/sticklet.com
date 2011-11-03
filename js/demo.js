for(var a in window.localStorage){
    if(/^notes_.*/.test(a)){
	window.localStorage.removeItem(a);
    }
}

var log=$("#login");
var pos=log.position();
var x=pos.left+log.width()+340;
var y=pos.top+33;

var note={id:"demo_note",x:700,y:395,z:100,subject:"Double-click to edit",content:"Double-click to edit"};
var online = false;
var token = "demo11";

window.localStorage.setItem("notes_demo",JSON.stringify({demo_note:note}));
username="demo";

$(document).ready(function(){
    $("body").height(Math.max($("body").height(),$(document).height()));
    var a=$("#demo_note");
    var b=a.children(".noteHeader").children("div");
    var c=a.children(".noteContent").children("blockquote");
    b.bind("dblclick",function(a){
	b.attr({contenteditable:true});
	b.css("cursor", "text");
	b.addClass("yesSelect outlined");
	b.focus();
	$(document).bind("click",function(a){
	    if(isEditable(b.get()))
		return;
	    b.attr({contenteditable:false});
	    $(document).unbind("click");
	    b.blur();
	})
    });
    b.bind("blur",function(a){
        b.attr({"contenteditable" : false}).css("cursor", "move").removeClass("yesSelect outlined");
    });
    c.bind("dblclick",function(a){
	c.attr({contenteditable:true});
	c.css("cursor", "text");
	c.addClass("yesSelect outlined");
	c.focus();
	$(document).bind("click",function(a){
	    if(isEditable(c.get()))return;
	    c.attr({contenteditable:false});
	    c.blur();
	    $(document).unbind("click");
	});
    });
    c.bind("blur",function(a){
        c.attr({"contenteditable" : false}).css("cursor", "move").removeClass("yesSelect outlined");
    });
    $("#noteArea").unbind("dblclick");
});