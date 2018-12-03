function vacantes(t) {
    if (t.checked) {
        document.body.className = "V";
    } else {
        document.body.className = "";
    }
}
function colapse() {
    var li = this.parentNode;
    if (li.className=="colapse") {
        this.textContent="[-]";
        li.className="";
    } else {
        this.textContent="[+]";
        li.className="colapse";
    }
}
document.addEventListener('DOMContentLoaded', function() {
    var i;
    var cols = document.getElementsByClassName("col");
    for (i=0; i<cols.length; i++) {
        cols[i].addEventListener('click', colapse);
    }
}, false);
