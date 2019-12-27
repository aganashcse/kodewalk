$(document).ready(function(){
    var code = $(".codemirror-textarea")[0];
     var editor=CodeMirror.fromTextArea(code, {
         lineNumbers : true
     });
     editor.setOption("mode", "python");
     editor.getDoc().setValue($("#script_template").val());
 });
 function not_developed_alert() { 
    window.alert("Apologies..\n" + 
        "This feature not yet developed! " +  
                 "Please do user login then crack the python logics\nTry this feature later some time"); 
}

var Ascii=true;
function isAscii(el) {
var i=0;
while ( i < el.value.length ){
if(el.value[i].charCodeAt(0) >= 0 && el.value[i].charCodeAt(0) <= 127 ){
i=i+1;
} 
else {
return false;
} 
}
return true;
}
function characterCount(el) {
if ( isAscii(el)){
Ascii=true;
}
else {
    window.alert("non-ascii");
    Ascii=false
}
return true;
}