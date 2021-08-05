import os, json, hashlib, hmac, github, markdown, redis, requests, stripe
from flask import Flask, render_template, redirect, flash, request, Markup
import flask_wtf, wtforms
from wtforms.validators import DataRequired, Email, ValidationError
from flask_wtf.file import FileField, FileAllowed, FileRequired
from keyboard import deserialise

with open('about.md', 'r') as about_file:
    about_text = Markup(markdown.markdown(about_file.read()))

images = [
    ('SA Lunchbar on M65-A, Side View', 'M65_Side'),
    ('GMK Carbon on Klippe, Front View', 'Klippe_Front'),
    ('DSA Lunchbar on Espectro, Front View', 'Espectro_Front'),
    ('GMK Carbon on Mech Mini 2, Top View', 'MM2_Top'),
    ('SA Lunchbar on Triangle, Top View', 'Triangle_Top'),
    ('GMK Carbon on Mech27, Side View', 'Mech27_Side'),
    ('SA Space Cadet (Freeform), Front View', 'Freeform_Front'),
    ('GMK Carbon (Freeform), Top View', 'Freeform_Top')
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
kle_text = '<span class="badge badge-warning">IMPORTANT</span> You <b>MUST</b> use this template: '
template_text = '<a id="{0}_{1}" class="template" target="_blank" rel="noreferrer" href="http://keyboard-layout-editor.com/#/gists/{2}">{1} on {0}</a>'
kle_text += ' '.join(template_text.format(k, p, g) for k, gists in templates.items() for p, g in gists.items())

# generate choices for upload fields
profiles = [(p, p) for p in ['SA', 'DSA', 'GMK']]
cameras = [(c, c+' View') for c in ['Top', 'Front', 'Side']]
materials = [(m, m) for m in ['Light Metal', 'Dark Metal', 'White Paint', 'Black Paint']]


app = Flask(__name__)
app.config.from_object('config')
github_api = github.Github(app.config['GITHUB_API_TOKEN'])  
stripe.api_key = app.config['STRIPE_SECRET_KEY']
queue = redis.from_url(app.config['REDIS_URL'])


class OrderForm(flask_wtf.FlaskForm):
    email = wtforms.StringField('Email Address', validators=[
        DataRequired(), Email(message='Valid email required')
    ])
    keyboard = wtforms.SelectField('Keyboard', choices=[
        ('Freeform', 'Freeform (No case)'),
        ('MM2', 'Mech Mini 2 (40%)'),
        ('Klippe', 'Klippe (60%)'),
        ('M65', 'M65-A (65%)'),
        ('Mech27', 'Mech27 (TKL)'),
        ('Espectro', 'Espectro (96%)'),
        ('Triangle', 'Triangle (Full-size)')
    ])
    profile = wtforms.SelectField('Keycap Profile', choices=profiles)
    kle = FileField('Layout JSON', validators=[
        FileRequired(), FileAllowed(['json'], 'Upload must be JSON')
    ], description=kle_text)
    camera = wtforms.SelectField('Camera Angle', choices=cameras)
    material = wtforms.SelectField('Case Material', choices=materials)
    background = wtforms.StringField('Background Color', default='#333333')
    stripeToken = wtforms.HiddenField('stripeToken')
    

    def validate_kle(form, field):
        if form.data['keyboard'] not in templates: return
        gist = templates[form.data['keyboard']][form.data['profile']]
        files = github_api.get_gist(gist).files
        layout = next(v for k, v in files.items() if k.endswith('.kbd.json'))
        
        template = deserialise(json.loads(layout.content))
        kle = deserialise(json.load(field.data))
        field.data.seek(0)
        if template != kle:
            raise ValidationError('Key layout must match provided template')


def add2queue(message):
    message['kle'] = json.load(message['kle'])
    message.pop('stripeToken', None)
    queue.lpush('orders', json.dumps(message))
    flash('Your order has been queued.')


def charge_card(token):
    return stripe.Charge.create(
        amount=500, currency='usd', source=token,
        description='3D render of keycap set design'
    )


def verify(sig):
    token = '{0}{1}'.format(sig['timestamp'], sig['token'])
    hmac_digest = hmac.new(
        key=app.config['MAILGUN_KEY'].encode('utf-8'),
        msg=token.encode('utf-8'), digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(sig['signature'], hmac_digest)


@app.route('/mailgun_hook', methods=['POST'])
def mailgun_hook():
    message = request.get_json()
    if not verify(message['signature']):
        return 'Improper verification request', 403
    requests.post(
        message['event-data']['storage']['url'],
        auth=('api', app.config['MAILGUN_KEY']),
        data={'to': app.config['ADMIN_EMAIL']}
    )
    return 'OK'


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = OrderForm(meta={'csrf': False})
    if form.validate_on_submit() and charge_card(form.data['stripeToken']):
        add2queue(form.data)
    elif request.method == 'POST':
        print('Error: {0}'.format(form.errors))
        flash('There was an error in your order. Your card was not charged.')

    return render_template(
        'index.html', images=images, about_text=about_text,
        form=form, stripeKey=app.config['STRIPE_PUBLISHABLE_KEY']
    )


if __name__ == '__main__':
    app.run(debug=True)
