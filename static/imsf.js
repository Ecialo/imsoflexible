var onFileSelected = function(event){
    var input = event.target;
    var fileName = input.value.split( '\\' ).pop();
    var label = input.nextElementSibling;

	if (fileName)
        input.className = "selected";
		label.innerHTML = fileName;
};

var onDataSubmit = function(event){
    var form = event.target;
    var submit = form.lastElementChild;
    submit.disabled = true;
    submit.value = "Loading...";
};