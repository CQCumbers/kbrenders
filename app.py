import os, json, glob, markdown, redis, stripe
import flask_wtf, wtforms, wtforms_components, wtforms.validators
from flask import Flask, render_template, redirect, flash, request, Markup
from flask_wtf.file import FileField, FileAllowed, FileRequired

with open('about.md', 'r') as about_file:
    about_text = Markup(markdown.markdown(about_file.read()))

images = [
    ('GMK Carbon on Mech27, Side View', 'Mech27_Side'),
    ('SA Lunchbar on Espectro, Front View', 'Espectro_Front'),
    ('GMK Carbon on Mech Mini 2, Top View', 'MM2_Top'),
    ('DSA Lunchbar on M65-A, Side View', 'M65_Side'),
    ('GMK Carbon on Klippe, Front View', 'Klippe_Front'),
    ('SA Lunchbar on Triangle, Top View', 'Triangle_Top')
]

# Use same kle templates for SA and DSA profiles
templates = {
    'MM2': {'SA': 'ea2a231112ffceae047494ac9a93e706', 'GMK': 'eed1f1854dda3999bcdd730f0143c627'},
    'Klippe': {'SA': 'f8369e8d6ae12c6d30bbf6db9731bca5', 'GMK': 'c2aedbf20e6a1ee5320a0f89b114d6da'},
    'M65': {'SA': '3ca3649e1d048134ddd0e835d1dd735b', 'GMK': '4319599274157d2a0dd0e38328b76878'},
    'Mech27': {'SA': '10629d008a99d8d6eb6f8c59414b5dd8', 'GMK': '6e6692825b348f40c040ca9750e469a8'},
    'Espectro': {'SA': '6b996bea3ebf8a85866ddea606e25de4', 'GMK': '6b996bea3ebf8a85866ddea606e25de4'},
    'Triangle': {'SA': 'b86a688e6502fcc910d4b32ca2fa642e', 'GMK': '11f7fc1a19c7f2210f560a93c8ab82a2'}
}
for k, gists in templates.items(): gists.update({'DSA': gists['SA']})
# Create upload help text from templates
kle_text = '<span class="badge badge-warning">IMPORTANT</span> You <strong>MUST</strong> use this template: '
template_text = '''
<a id="{0}_{1}" class="template" target="_blank" href="http://keyboard-layout-editor.com/#/gists/{2}">
  {1} on {0}
</a>
'''
kle_text += ' '.join(template_text.format(k, p, g) for k, gists in templates.items() for p, g in gists.items())


app = Flask(__name__)
app.config.from_object('config')
stripe.api_key = app.config['STRIPE_SECRET_KEY']
queue = redis.from_url(app.config['REDIS_URL'])


class OrderForm(flask_wtf.FlaskForm):
    email = wtforms.StringField('Email Address', validators=[
        wtforms.validators.DataRequired(), wtforms.validators.Email(message='Valid email required')
    ])
    keyboard = wtforms.SelectField('Keyboard', choices=[
        ('MM2', 'Mech Mini 2 (40%)'),
        ('Klippe', 'Klippe (60%)'),
        ('M65', 'M65-A (65%)'),
        ('Mech27', 'Mech27 (TKL)'),
        ('Espectro', 'Espectro (96%)'),
        ('Triangle', 'Triangle (Full-size)')
    ])
    profile = wtforms.SelectField('Keycap Profile', choices=[(p, p) for p in ['SA', 'DSA', 'GMK']])
    kle = FileField('Layout JSON', validators=[
        FileRequired(), FileAllowed(['json'], 'Upload must be JSON')
    ], description=kle_text)
    camera = wtforms.SelectField('Camera Angle', choices=[(c, c+' View') for c in ['Side', 'Top', 'Front']])
    background = wtforms_components.ColorField('Background Color', default='#ffffff')
    stripeToken = wtforms.HiddenField('stripeToken')


def add2queue(message):
    message['background'] = message['background'].hex
    message['kle'] = json.load(message['kle'])
    message.pop('csrf_token', None)
    message.pop('stripeToken', None)
    queue.lpush('orders', json.dumps(message))
    flash('Your order has been queued.')


def charge_card(token):
    return stripe.Charge.create(
        amount=1000, currency='usd', source=token,
        description='3D render of keycap set design'
    )


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = OrderForm()
    if form.validate_on_submit() and charge_card(form.data['stripeToken']):
        add2queue(form.data)
    elif request.method == 'POST':
        flash('There was in error in your order form. Your card was not charged.')

    return render_template(
        'index.html', images=images, about_text=about_text,
        form=form, stripeKey=app.config['STRIPE_PUBLISHABLE_KEY']
    )


if __name__ == '__main__':
    app.run(debug=True)
