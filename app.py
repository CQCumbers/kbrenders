import os, json, glob, markdown, redis, stripe
import flask_wtf, wtforms, wtforms_components, wtforms.validators
from flask import Flask, render_template, redirect, flash, request, Markup
from flask_wtf.file import FileField, FileAllowed, FileRequired

app = Flask(__name__)
app.config.from_object('config')
stripe.api_key = app.config['STRIPE_SECRET_KEY']
queue = redis.from_url(app.config['REDIS_URL'])

about_text = '''
#### What does kbrenders do?

If you're designing a custom set of mechanical keyboard keycaps for a group buy, you'll probably need visualizations of what the set will look like before it is manufactured. In the early stages a tool like [kle-render](http://kle-render.herokuapp.com) can be very useful, but eventually you may want something more convincing to show. kbrenders can automatically create photorealistic images of keycap set designs within 24 hours. It works by turning customized keyboard-layout-editor templates into blender scenes, which can then be ray-traced overnight on a cloud server. The result is low-cost, high-realism 3D renders that are already being used in set designs like DSA Alchemy and GMK Her.

#### How do I use kbrenders?

You should first fill in the form above with a keyboard, and keycap profile for your render, then start editing the provided keyboard-layout-editor template. Keep in mind that arbitrary key layouts - as well as custom CSS - are *not* supported. What can be modified are colors and legends, which can include most unicode glyphs and character picker symbols. Custom legend images will also work as long as they take up the entire surface of a keycap. If you are unsure how your legends will render, you can preview exactly how they will look using [kle-render](http://kle-render.herokuapp.com) (kbrenders uses the same code for generating legends). After customizing the template to your satisfaction, download the JSON file from keyboard-layout-editor using the top right button and upload it into the Layout JSON form field. You can also change the camera angle and background color - click on the sample renders for a general idea of what these options do.

#### What if my layout doesn't render correctly?
If you are having problems with a specific render, you can email me at mail@kbrenders.com. Please attach the JSON file and other settings used in your order - I need them to be able to help you. In most cases I can redo the render or refund you if the original result was not satisfactory, though this is a hobby for me so it may take a few days before I can respond. In my experience, the most common reason for incorrect renders is using a different keyboard-layout-editor layout than the template, so it may be worth it to double check that you haven't changed any key sizes or locations before submitting. For general bug reports, questions, and feature requests you can also message me on reddit as [/u/CQ_Cumbers](http://reddit.com/u/CQ_Cumbers) or on geekhack as CQ_Cumbers. Service outages, changelogs, and other information will be posted on the **[geekhack thead](https://geekhack.org/index.php?topic=92666.0)**. 

*Many thanks to RAMA, Mech27, Simen, and Mechkeys.ca for their keyboard models.*
'''

templates = [
    ('MM2', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/ea2a231112ffceae047494ac9a93e706'),
    ('MM2', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/ea2a231112ffceae047494ac9a93e706'),
    ('MM2', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/eed1f1854dda3999bcdd730f0143c627'),
    ('Klippe', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/f8369e8d6ae12c6d30bbf6db9731bca5'),
    ('Klippe', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/f8369e8d6ae12c6d30bbf6db9731bca5'),
    ('Klippe', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/c2aedbf20e6a1ee5320a0f89b114d6da'),
    ('M65', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/3ca3649e1d048134ddd0e835d1dd735b'),
    ('M65', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/3ca3649e1d048134ddd0e835d1dd735b'),
    ('M65', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/4319599274157d2a0dd0e38328b76878'),
    ('Mech27', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/10629d008a99d8d6eb6f8c59414b5dd8'),
    ('Mech27', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/10629d008a99d8d6eb6f8c59414b5dd8'),
    ('Mech27', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/6e6692825b348f40c040ca9750e469a8'),
    ('Espectro', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/6b996bea3ebf8a85866ddea606e25de4'),
    ('Espectro', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/6b996bea3ebf8a85866ddea606e25de4'),
    ('Espectro', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/6a03012a82e7bbca14db635142913a7f'),
    ('Triangle', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/b86a688e6502fcc910d4b32ca2fa642e'),
    ('Triangle', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/b86a688e6502fcc910d4b32ca2fa642e'),
    ('Triangle', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/11f7fc1a19c7f2210f560a93c8ab82a2')
]

t_str = '<a id="{0}_{1}" class="template" target="_blank" href="{2}">{1} on {0}</a>'
kle_text = '<span class="badge badge-warning">IMPORTANT</span> You <strong>MUST</strong> use this template: '
kle_text += ' '.join(t_str.format(*t) for t in templates)


class OrderForm(flask_wtf.FlaskForm):
    email = wtforms.StringField('Email Address',
        validators=[wtforms.validators.DataRequired(), wtforms.validators.Email(message="Valid email required")],
    )
    keyboard = wtforms.SelectField('Keyboard', choices=[
        ('MM2', 'Mech Mini 2 (40%)'),
        ('Klippe', 'Klippe (60%)'),
        ('M65', 'M65-A (65%)'),
        ('Mech27', 'Mech27 (TKL)'),
        ('Espectro', 'Espectro (96%)'),
        ('Triangle', 'Triangle (Full-size)')
    ])
    profile = wtforms.SelectField('Keycap Profile', choices=[
        ('SA', 'SA'),
        ('GMK', 'GMK'),
        ('DSA', 'DSA')
    ])
    kle = FileField('Layout JSON', validators=[
        FileRequired(),
        FileAllowed(['json'], 'Upload must be JSON')
    ], description=kle_text)
    camera = wtforms.SelectField('Camera Angle', choices=[
        ('Side', 'Side View'),
        ('Top', 'Top View'),
        ('Front', 'Front View')
    ])
    background = wtforms_components.ColorField('Background Color', default='#ffffff')
    stripeToken = wtforms.HiddenField('stripeToken')


def add2queue(message):
    message['background'] = message['background'].hex
    message['kle'] = message['kle'].read().decode('utf-8')
    message.pop('csrf_token', None)
    message.pop('stripeToken', None)

    queue.lpush('orders', json.dumps(message))
    flash('Your order has been queued.')


def charge_card(token):
    charge = stripe.Charge.create(
        amount=1000,
        currency='usd',
        description='3D render of keycap set design',
        source=token,
    )
    return charge


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = OrderForm()
    images = [
        ('GMK Carbon on Mech27, Side View', 'Mech27_Side'),
        ('SA Lunchbar on Espectro, Front View', 'Espectro_Front'),
        ('GMK Carbon on Mech Mini 2, Top View', 'MM2_Top'),
        ('DSA Lunchbar on M65-A, Side View', 'M65_Side'),
        ('GMK Carbon on Klippe, Front View', 'Klippe_Front'),
        ('SA Lunchbar on Triangle, Top View', 'Triangle_Top')
    ]
    if not form.validate_on_submit():
        if request.method == 'POST':
            flash('There was in error in your order form. Your card was not charged.')
        about_rendered = Markup(markdown.markdown(about_text))
        return render_template(
            'index.html',
            images=images,
            about_text=about_rendered,
            form=form,
            stripeKey=app.config['STRIPE_PUBLISHABLE_KEY']
        )
    if charge_card(form.data['stripeToken']):
        add2queue(form.data)
    else:
        flash('Your payment could not be processed. Your card was not charged.')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
