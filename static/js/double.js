//define template
var template = $('#sections .section:first').clone();

//define counter
var sectionsCount = 1;

//add new section
$('body').on('click', '.addsection', function() {

    //increment
    sectionsCount++;

    //loop through each input
    var section = template.clone().find(':input').each(function(){

        //update id
        this.name = this.name + sectionsCount;

    }).end();

    section.find('.bootstrap-select').replaceWith(function() { return $('select', this); });
    section.find('.selectpicker').selectpicker();
    $( '.addsection' ).last().remove()
    section.appendTo('#sections');
    return false;
});

$('#sections').on('click', '.remove:last', function() {
    //fade out section
    $(this).parent().fadeOut(1, function(){
        //remove parent element (main section)
        $(this).parent().remove();
        sectionsCount--;
        $( '.section .form-group' ).last().append('<button type="button" class="btn btn-primary addsection">add section</button>');
        return false;
    });
    return false;
});

//remove section
$('#sections').on('click', '.remove', function() {
    //fade out section
    $(this).parent().fadeOut(1, function(){
        //remove parent element (main section)
        $(this).parent().remove();
        sectionsCount--;
        return false;
    });
    return false;
});