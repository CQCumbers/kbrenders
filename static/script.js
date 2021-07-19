$('.custom-file-input').on('change', function() {
  let fileName = $(this).val().split('\\').pop();
  $(this).next('.custom-file-label').html(fileName || 'Choose file');
});
$('.custom-file-input').change();

function showTemplate() {
  $('.template').addClass('d-none');
  var selected = $('#keyboard').val()+'_'+$('#profile').val();
  $('#'+selected).removeClass('d-none');
  if ($('#keyboard').val() == 'Freeform') {
    $('.template-warn').addClass('d-none');
  } else {
    $('.template-warn').removeClass('d-none');
  }
}

$('#keyboard, #profile').change(showTemplate);
$('#order-form').submit(function(e) {
  // if triggered by human
  if (e.originalEvent !== undefined) {
    handler.open({email: $('#email').val()});
    e.preventDefault();
  }
});

$('.formcolorpicker').each(function() {
  $(this).colorpicker({ useAlpha: false });
});

var handler = StripeCheckout.configure({
  key: stripeKey,
  locale: 'auto',
  name: 'kbrenders',
  description: '3D render of keycap set design',
  amount: 500,
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

lightbox.option({
  'resizeDuration': 200,
  'fadeDuration': 200,
  'imageFadeDuration': 0,
  'wrapAround': true,
});

$(document).on('click', '[data-toggle="lightbox"]', function(e) {
    e.preventDefault();
    $(this).ekkoLightbox();
});

showTemplate();
