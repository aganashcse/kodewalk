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
function test_run_code() { 
    document.getElementById("test_run").value = "true";
    document.getElementById('submit_form').submit(); 
}
