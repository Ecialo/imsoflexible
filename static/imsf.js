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

(function (){
    
    var updateInterval = null;

    var rebuildTaskList = function(data){
        $("#taskListContainer").css("display", data.length > 0 ? "block" : "none");
    
        var table = $("#taskList");
        var rows = table.find("tr");
        Array.prototype.shift.apply(rows); // first row is a header
    
        // Remove deleted tasks from list
        for (var i = 0; i < rows.length; i ++){
            var ex = data.some(function(task){
                return task["id"] == rows[i].id;
            });
            
            if (!ex){
                $(rows[i]).remove()
            }
        }
        
        var completed = true;
        
        // Update & add tasks
        for (var i = 0; i < data.length; i ++){
            var row = $("#" + data[i]["id"])[0];
            if (!row){
                row = document.createElement("tr");
                row.id = data[i]["id"];
                row.innerHTML = '<td></td><td><div class="fileName"></div></td>';
                table.append(row);
            }
            var s = data[i]["state"];
            var p = data[i]["progress"];
            row.firstElementChild.innerHTML = (
                s == 0 ? "Queueing" : 
                s == 1 ? "Processing" + (p == 0 ? "" : " (" + p + "%)") :
                s == 2 ? "Completed" : 
                ""
            );

            if (s != 2){
                $(row).find(".fileName").html(data[i]["name"]);
            }else{
                var ln = $("<a>", {
                    href: "./file?id=" + data[i]["id"],
                    text: data[i]["name"]
                });
                ln.click(linkClicked);
                $(row).find(".fileName").html(ln);
            }
            
            if (s != 2) completed = false;
        }
        
        if (completed) clearInterval(updateInterval);
    };

    var linkClicked = function(event){
        var t = event.target;
        $(t).closest("tr").remove();

        var rows = $("#taskList").find("tr");
        Array.prototype.shift.apply(rows); // first row is a header
        if (rows.length == 0){
            $("#taskListContainer").css("display", "none");
        }
    };
    
    var downloadStats = function(){
        $.getJSON("./stats",rebuildTaskList);
    };
    
    $(function(){
        updateInterval = setInterval(downloadStats, 10000);
        downloadStats();
    });
})();
