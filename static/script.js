function showTemplate() {
  $('.template').addClass('d-none');
  var selected = $('#keyboard').val()+'_'+$('#profile').val();
  $('#'+selected).removeClass('d-none');
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
    $('#order-form').append($(token));
    $('#order-form').submit();
  }
});

$(document).on('click', '[data-toggle="lightbox"]', function(e) {
    e.preventDefault();
    $(this).ekkoLightbox();
});

$('#keyboard, #profile').change(showTemplate);
$('#order-form').submit(function(e) {
  // if triggered by human
  if (e.originalEvent !== undefined) {
    handler.open({email: $('#email').val()});
    e.preventDefault();
  }
});

showTemplate();
