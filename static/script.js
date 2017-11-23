function showTemplate() {
  $('.template').addClass('hidden');
  var selected = $('#keyboard').val()+'_'+$('#profile').val();
  console.log(selected);
  $('#'+selected).removeClass('hidden');
}

$('#keyboard, #profile').change(showTemplate);
showTemplate()
