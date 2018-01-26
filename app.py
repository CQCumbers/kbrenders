from flask import Flask, render_template, redirect, flash, request, Markup

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SelectField, HiddenField
from wtforms_components import ColorField
from wtforms.validators import DataRequired

import os, json, glob, markdown, stripe, boto3

application = Flask(__name__)
app = application # for compatibility with EB
app.config.from_object('config')
stripe.api_key = os.environ['STRIPE_SECRET_KEY']
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName='kbrenders-queue.fifo')


about_text = '''
### What does kbrenders do?

kbrenders is an automated service for 3D rendering custom keycap set designs. It works by parsing certain [keyboard-layout-editor](http://keyboard-layout-editor.com) designs into blender scenes that can then be rendered. It is (currently) rather limited in what it can do compared to a professional artist, but it is considerably faster and cheaper. Compared to [kle-render](http://kle-render.herokuapp.com), final output is much more realistic due to kbrenders actually ray tracing every request in blender on cloud servers. The render fee allows me to keep this service running - unlike image compositing, ray tracing is computationally expensive so server costs are more of a concern.

### What features are supported?

You must start with one of the provided keyboard-layout-editor templates - custom layouts are not supported. Colors and legend customizations are supported, as well as most unicode glyphs and character picker symbols; besides layout, custom CSS and external images are also not supported. Changes to keycap profile and background color in keyboard-layout-editor are not honored - use the background color and keycap profile fields in the order form instead.

### How should I report bugs or request features?

Emails should be directed to mail@kbrenders.com. If you are having problems with a specific layout it would help enormously if you could attach the JSON file and the settings used in your order. For general questions you can also message me on reddit as [/u/CQ_Cumbers](http://reddit.com/u/CQ_Cumbers) or on geekhack as CQ_Cumbers.

Information about service outages, changelogs, and other information will be posted on the [geekhack thead](https://geekhack.org/index.php?topic=92666.0). 

**Many thanks to RAMA, Photekq, and Mechkeys.ca for their keyboard models.**
'''

templates = [('M65', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/3ca3649e1d048134ddd0e835d1dd735b'),
        ('M65', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/3ca3649e1d048134ddd0e835d1dd735b'),
        ('M65', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/4319599274157d2a0dd0e38328b76878'),
        ('TEK80', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/10629d008a99d8d6eb6f8c59414b5dd8'),
        ('TEK80', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/10629d008a99d8d6eb6f8c59414b5dd8'),
        ('TEK80', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/6e6692825b348f40c040ca9750e469a8'),
        ('MM2', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/ea2a231112ffceae047494ac9a93e706'),
        ('MM2', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/ea2a231112ffceae047494ac9a93e706'),
        ('MM2', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/eed1f1854dda3999bcdd730f0143c627'),
        ('Espectro', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/6b996bea3ebf8a85866ddea606e25de4'),
        ('Espectro', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/6b996bea3ebf8a85866ddea606e25de4'),
        ('Espectro', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/6a03012a82e7bbca14db635142913a7f')]


class OrderForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired()],
            description="We'll email the final render to this address within 24 hours.")
    keyboard = SelectField('Keyboard', choices=[('M65', 'M65'), ('TEK80', 'TEK80'), ('MM2', 'Mech Mini 2'), ('Espectro', 'Espectro')])
    profile = SelectField('Keycap Profile', choices=[('SA', 'SA'), ('GMK', 'GMK'), ('DSA', 'DSA')])
    kle = FileField('KLE JSON', validators=[FileRequired(), FileAllowed(['json'], 'Upload must be JSON')],
            description='<b>You MUST use this template: {}</b><br/>You can preview legend appearance using <a href="http://kle-render.herokuapp.com">kle-render</a>'.format(
                ' '.join(['<a id="{}" class="template" target="_blank" href="{}">{}</a>'.format(t[0]+'_'+t[1], t[2], t[1]+' on '+t[0]) for t in templates])))
    camera = SelectField('Camera Angle', choices=[('Side', 'Side View'), ('Top', 'Top View'), ('Front', 'Front View')])
    background = ColorField('Background', default='#ffffff')
    stripeToken = HiddenField('stripeToken')

def add2queue(message):
    message['background'] = message['background'].hex
    message['kle'] = message['kle'].read().decode('utf-8')

    queue.send_message(MessageBody=json.dumps(message), MessageGroupId='render_request')
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
    images = [('SA Lunchbar on RAMA M65-A, Side View', 'M65_Side.png'),
            ('SA Lunchbar on RAMA M65-A, Front View', 'M65_Front.png'),
            ('GMK Carbon on TEK80, Side View', 'TEK80_Side.png'),
            ('GMK Carbon on TEK80, Top View', 'TEK80_Top.png')]
    if not form.validate_on_submit():
        if request.method == 'POST':
            flash('There was in error in your order form.')
        about_rendered = Markup(markdown.markdown(about_text))
        return render_template('index.html', images=images, about_text=about_rendered,
                form=form, stripeKey=os.environ['STRIPE_PUBLISHABLE_KEY'])
    if charge_card(form.data['stripeToken']):
        add2queue({i:form.data[i] for i in form.data if i != 'csrf_token'})
    else:
        flash('Your payment could not be processed')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True) # Use debug=False on actual server
