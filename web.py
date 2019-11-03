from jinja2 import Environment, PackageLoader, select_autoescape
from sanic import Sanic, response
from sanic.response import json, html
import cv2

import shared


# define the environment for the Jinja2 templates
env = Environment(
    loader=PackageLoader('main', 'templates'),
    autoescape=select_autoescape(['html', 'xml', 'tpl', 'j2'])
)


# a function for loading an HTML template from the Jinja environment
def template(tpl, **kwargs):
    template = env.get_template(tpl)
    return html(template.render(kwargs))


app = Sanic()


@app.route("/")
async def mainList(request):
    return template('index.j2', images = shared.framebuffer, processed = shared.get_counter('images_processed'), skipped = shared.get_counter('images_skipped'), avg = shared.get_counter('images_time') / shared.get_counter('images_processed'), skip_avg = shared.get_counter('skipped_time') / shared.get_counter('images_skipped'), total = shared.get_counter('images_time'), stream_resets = shared.get_counter('stream_resets'), size = shared.get_size())

@app.route('/snapshot/<tag>')
async def tag_handler(request, tag):
    if(tag in shared.framebuffer):
        _, jpg = cv2.imencode('.jpg', shared.framebuffer[tag])
        return response.raw(jpg, content_type='image/jpeg')
    else:
        return response.html('No image')




def begin():
    app.run(host="0.0.0.0", port=8000)