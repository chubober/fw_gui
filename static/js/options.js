var opt_text = document.getElementById("text_cols");
document.getElementById("sel_cols").addEventListener("change", function() {
    var selected_sel = [...this.selectedOptions]
                    .map(option => option.value);
    for (var i = 0; i < opt_text.children.length; i++) {
        if (selected_sel.includes(opt_text.children[i].value)) {
            opt_text.children[i].disabled = true;
        }
        else if (!selected_sel.includes(opt_text.children[i].value)) {
            opt_text.children[i].disabled = false;
        }
    }
    $('#text_cols').selectpicker('refresh');
});

var opt_sel = document.getElementById("sel_cols");
document.getElementById("text_cols").addEventListener("change", function() {
    var selected_text = [...this.selectedOptions]
                    .map(option => option.value);
    for (var i = 0; i < opt_sel.children.length; i++) {
        if (selected_text.includes(opt_sel.children[i].value)) {
            opt_sel.children[i].disabled = true;
        }
        else if (!selected_text.includes(opt_sel.children[i].value)) {
            opt_sel.children[i].disabled = false;
        }
    }
    $('#sel_cols').selectpicker('refresh');
});
