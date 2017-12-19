function showTemplate() {
  $('.template').addClass('hidden');
  var selected = $('#keyboard').val()+'_'+$('#profile').val();
  $('#'+selected).removeClass('hidden');
}

var handler = StripeCheckout.configure({
  key: stripeKey,
  locale: 'auto',
  name: 'kbrenders',
  description: '3D render of keycap set design',
  amount: 1000,
  zipCode: true,
  token: function(t) {
    var token = $('<input />')
      .attr('type', 'hidden')
      .attr('name', 'stripeToken')
      .val(t.id);
    $('#orderform').append($(token));
    $('#orderform').submit();
  }
});

$('#keyboard, #profile').change(showTemplate);
$('#orderform').submit(function(e) {
  // if triggered by human
  if (e.originalEvent !== undefined) {
    handler.open({email: $('#email').val()});
    e.preventDefault();
  }
});
showTemplate();
