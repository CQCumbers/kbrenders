from flask import Flask, render_template, redirect, flash, request

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms_components import ColorField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed, FileRequired

import boto3, os, json, glob

app = Flask(__name__)
app.config.from_object('config')
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName='kbrenders-queue.fifo')

class OrderForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired()], description="We'll email the final render to this address within 24 hours.")
    keyboard = SelectField('Keyboard', choices=[('M65', 'M65'), ('TEK80', 'TKL')])
    profile = SelectField('Keycap Profile', choices=[('SA', 'SA'), ('GMK', 'GMK')])
    kle = FileField('KLE JSON', validators=[FileRequired(), FileAllowed(['json'], 'Upload must be JSON')], description="Use one of the following templates: <a href='http://www.keyboard-layout-editor.com/#/gists/3ca3649e1d048134ddd0e835d1dd735b'>M65</a>, <a href='http://www.keyboard-layout-editor.com/#/gists/6e6692825b348f40c040ca9750e469a8'>TKL</a>.")
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
    images = glob.glob('static/renders/*.png')
    if not form.validate_on_submit():
        if request.method == 'POST':
            flash('There was in error in your order form.')
        return render_template('index.html', images=images, form=form)
    add2queue(form.data)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True) # Use debug=False on actual server
