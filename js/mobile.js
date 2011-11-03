/*
*   COPYRIGHT 2011 Vincent Dumas
*   COPYRIGHT 2011 Alex Zylman
*
*/

"use strict";

function startDrag( event, note ){

    var over = $("<div />", {
	"class" : "overlay"
    });
    $("body").append ( over );
    over.fadeIn( "fast" );
    over.bind( "click", function ( event ) {
	if ( event.currentTarget == event.target ) {
	    if ( !! notes[note.id] ) {
		writeNote ( note );
	    } else {
		$("#tmp_" + note.id).remove();
	    }
	    over.fadeOut( "fast", function(){
		over.remove();
	    });
	}
    });

    writeMobile ( note, over );

}

function getNotes(){
    $.ajax ({
	"url" : "/notes",
	"async" : true,
	"type" : "GET",
	"dataType" : "json",
	"success" : function( resp ) {
            var tmp = {};
            $.each(resp, function(index) {
		writeNote ( resp[index], false );
		delete notes[resp[index].id];
		tmp[resp[index].id] = resp[index];
            });
            for ( var d in notes ){
		if ( notes.hasOwnProperty ( d ) ) {
		    $( "#" + notes[d].id ).remove();
		}
	    }
            notes = tmp;
            dumpNotes();
	}
    });
}

function compare ( note ) {

    var n = notes[note.id];
    if ( n === undefined || n === null ) { return false; }
    var pos = { "left" : n.x, "top" : n.y };
    if ( pos.left === offleft ) {
	if ( (pos.top-45) % 35 === 0 ) {
	    note.x = n.x;
	    note.y = n.y;
	    note.z = n.z;
	    return true;
	}
    }
    return false;
	
}

var offset = 45;
var mobZ = 0;
var offleft = 37;

function writeNote ( note ) {

    if ( ! compare ( note ) ){ 
	note.x = offleft;
	note.y = offset;
	note.z = mobZ++;
    }

    var elm = $('<div />',  {
        "class" : "note",
	"id" : "tmp_" + note.id
    });

    elm.css({
        'left' : note.x,
        'top' : note.y,
	"zIndex" : note.z,
        'backgroundColor' : note.color
    });

    offset += 35;

    elm.bind('click', function(event) {
	event.preventDefault();
        startDrag( event, note );
    });

    var h = $('<div />', {
        "class" : "noteHeader"
    });
    var s = $('<div />');
    s.html(note.subject);
    h.append( s );
    elm.append( h );
    elm.append( $("<hr/>" ) );
    var c = $('<div />', {
        "class" : 'noteContent'
    });
    var b = $('<blockquote />');
    b.html(note.content);
    c.append ( b );
    elm.append ( c );
    $( "#tmp_" + note.id ).remove();
    $("#noteArea").append ( elm );
}

function writeMobile ( note, over ) {

    var elm = $('<div />',  {
        "class" : "note",
        "id" : note.id
    });

    elm.css({
        'backgroundColor' : note.color,
	"margin" : "auto",
	"color" : "black",
	"top" : 45,
	"left" : offleft + 5
    });

    var h = $('<div />', {
        "class" : "noteHeader"
    });

    var s = $('<div />');
    s.bind("blur", function(event) {
        closeSave(event, $(this));
        $(this).attr({"contenteditable" : false});
    });
    s.bind( "keypress", function ( event ) {
	if (event.keyCode == 13 ) {
            event.preventDefault();
            event.stopPropagation();
            return;
	}
    });
    s.bind( "click", function ( event ) {
	event.preventDefault();
	if ( ! online ){ return; }
	s.attr({"contenteditable" : true});
	s.focus();
	$(document).bind ( "click", function( event ) {
            if ( isEditable ( event.target ) ){ return; }
            event.stopPropagation();
	    s.blur();
            $(document).unbind( "click" );
	});
    });
    s.html(note.subject);

    var o = $('<div />', {
        "class" : "options"
    });
    o.bind( "click", function(event) {
	unToggle();
	event.preventDefault();
	event.stopPropagation();
	dropDown( elm );
    });
    elm.append( o );
    o.css({"display":"inline"});

    h.append( s );
    elm.append( h );

    elm.append( $("<hr/>" ) );
    var c = $('<div />', {
        "class" : 'noteContent'
    });
    var b = $('<blockquote />');
    b.bind ( "blur", function( event ) {
        closeSave(event, b);
        b.attr({"contenteditable" : false});
    });
    b.bind ( "click", function( event ) {
	if ( ! online ){ return; }
	b.attr({"contenteditable" : true});
	b.focus();
	$(document).bind ( "click", function( event ) {
            if ( isEditable ( event.target ) ){ return; }
            event.stopPropagation();
            b.attr({"contenteditable" : false});
            $(document).unbind( "click" );
            closeSave( event, b );
	});
    });
    b.html(note.content);

    c.append ( b );
    elm.append ( c );

    elm.css({"display":"none"});
    over.append ( elm );
    elm.fadeIn( 350 );

}

function saveNote(){}
function deleteNote(){}