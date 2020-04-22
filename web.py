import pprint
import time

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

app.static('/static', './static')

@app.route("/")
async def mainList(request):
    filtered = {}
    for (k, v) in shared.framebuffer.items():
        if "_"  not in k:
            filtered[k] = v
    return template('index.html', images = filtered, processed = shared.get_counter('images_processed'), skipped = shared.get_counter('images_skipped'), avg = shared.get_counter('images_time') / shared.get_counter('images_processed'), skip_avg = shared.get_counter('skipped_time') / shared.get_counter('images_skipped'), diff_avg = shared.get_counter('total_skip_diff') / shared.get_counter('images_skipped'), diff_avg2 = shared.get_counter('total_diff') / shared.get_counter('total_processed'), total = shared.get_counter('images_time'), stream_resets = shared.get_counter('stream_resets'), size = shared.get_size())

@app.route("/video/<tag>")
async def mainList(request, tag):
    return template('video.html', tag = tag)



@app.route('/snapshot/<tag>')
async def tag_handler(request, tag):
    if(tag in shared.framebuffer):
        _, jpg = cv2.imencode('.jpg', shared.framebuffer[tag])
        return response.raw(jpg, content_type='image/jpeg', headers={'Cache-Control': 'no-store'})
    else:
        return response.html('No image')

@app.route("/stats")
async def mainList(request):
    return response.html(pprint.pformat(shared.frame_stats))

@app.route("/munin")
async def mainList(request):
    result = {}
    for (k, v) in shared.frame_stats.items():
        if len(v) > 1000:
            shared.logger.info("Trimming to 1000")
            shared.frame_stats[k] = v[-1000:]

    for (k, v) in shared.frame_stats.items():
        frames = 0
        diff = 0
        pprint.pprint(k);
        pprint.pprint(len(v));

        for stat in v:
            if(time.time() - stat['time'] < 60 * 5):
                frames = frames + 1
                diff = diff + stat['stat']


        pprint.pprint(frames)
        result[k] = diff / frames


    return template('munin.html', stats = result)


def begin():
    app.run(host="0.0.0.0", port=8000)