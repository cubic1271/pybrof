__author__ = 'clarkg1'
import time

from top.render import Renderer
from prof.parse import ProfileLog

if __name__ == '__main__':
    log = ProfileLog('./prof.log')
    render = Renderer()
    try:
        for entry in log:
            render.update(entry)
            time.sleep(5)
    except KeyboardInterrupt:
        render.cleanup()
