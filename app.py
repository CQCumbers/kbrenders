from flask import Flask, render_template, redirect, flash, request, Markup

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SelectField
from wtforms_components import ColorField
from wtforms.validators import DataRequired

import boto3, os, json, glob, markdown

app = Flask(__name__)
app.config.from_object('config')
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName='kbrenders-queue.fifo')



about_text = '''
### What does kbrenders do?

kbrenders is an automated service for 3D rendering certain [keyboard-layout-editor](http://keyboard-layout-editor.com) designs. It is (currently) rather limited in what it can do compared to a professional artist, but it is considerably faster and cheaper. Compared to [kle-render](http://kle-render.herokuapp.com), final output is much more realistic due to kbrenders actually ray tracing every request in blender. While for now it is a free service, I may have to charge a small fee for renders in the future depending on server costs.

### What features are supported?

You must start with one of the provided keyboard-layout-editor templates - custom layouts are not supported. Colors and legend customizations are supported, as well as most unicode glyphs and character picker symbols; besides layout, custom CSS and external images are also not supported. Changes to keycap profile and background color in keyboard-layout-editor are not honored - use the background color and keycap profile fields in the order form instead.

### How should I report bugs or request features?

Emails should be directed to mail@kbrenders.com. If you are having problems with a specific layout it would help enormously if you could attach the JSON file and the settings used in your order. For general questions you can also message me on reddit as [/u/CQ_Cumbers](http://reddit.com/u/CQ_Cumbers) or on geekhack as CQ_Cumbers.

**Many thanks to RAMA for his M65-A model and Photekq for his TEK-80 model**
'''

templates = [('M65', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/3ca3649e1d048134ddd0e835d1dd735b'),
        ('M65', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/3ca3649e1d048134ddd0e835d1dd735b'),
        ('M65', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/4319599274157d2a0dd0e38328b76878'),
        ('TEK80', 'SA', 'http://www.keyboard-layout-editor.com/#/gists/10629d008a99d8d6eb6f8c59414b5dd8'),
        ('TEK80', 'DSA', 'http://www.keyboard-layout-editor.com/#/gists/10629d008a99d8d6eb6f8c59414b5dd8'),
        ('TEK80', 'GMK', 'http://www.keyboard-layout-editor.com/#/gists/6e6692825b348f40c040ca9750e469a8')]



class OrderForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired()],
            description="We'll email the final render to this address within 24 hours.")
    keyboard = SelectField('Keyboard', choices=[('M65', 'M65'), ('TEK80', 'TEK80')])
    profile = SelectField('Keycap Profile', choices=[('SA', 'SA'), ('GMK', 'GMK'), ('DSA', 'DSA')])
    kle = FileField('KLE JSON', validators=[FileRequired(), FileAllowed(['json'], 'Upload must be JSON')],
            description='<b>You MUST use this template: {}</b><br/>You can preview legend appearance using <a href="http://www.kle-render.herokuapp.com">kle-render</a>'.format(
                ' '.join(['<a id="{}" class="template" target="_blank" href="{}">{}</a>'.format(t[0]+'_'+t[1], t[2], t[1]+' on '+t[0]) for t in templates])))
    camera = SelectField('Camera Angle', choices=[('Side', 'Side View'), ('Top', 'Top View'), ('Front', 'Front View')])
    background = ColorField('Background', default='#ffffff')

def add2queue(message):
    message['background'] = message['background'].hex
    message['kle'] = message['kle'].read().decode('utf-8')

    queue.send_message(MessageBody=json.dumps(message), MessageGroupId='render_request')
    flash('Your order has been queued.')

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
        return render_template('index.html', images=images, form=form, about_text=about_rendered)
    add2queue(form.data)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True) # Use debug=False on actual server
