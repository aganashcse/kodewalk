window.onload = function() {
    var code_editor=document.getElementById('code').value;
    this.console.log(code_editor.split("\r").length);
    var script_template = this.document.getElementById('script_template').value;
    if(code_editor.split("\r").length<2){
        document.getElementById('code').innerHTML = script_template;
    }
    this.console.log(script_template)
    this.console.log("sep,")
    this.console.log(document.getElementById('code').value)
  };