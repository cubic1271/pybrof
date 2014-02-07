__author__ = 'clarkg1'
import time
from optparse import OptionParser

from top.render import Renderer
from prof.parse import ProfileLog

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-f', '--file', dest='file', metavar='LOGFILE', help='target file (normally "/path/to/prof.log")', default='./prof.log')
    parser.add_option('-r', '--review', dest='review', help='manually advance through log entries to allow for easier review', action='store_true', default=False)
    (options, args) = parser.parse_args()
    log = ProfileLog(options.file)
    render = Renderer()
    render.advance = options.review
    try:
        while not render.finished:
            entry = None
            if render.advance or render.fetch:
                entry = log.read()
            if render.fetch:
                render.fetch = False
            render.update(entry)
            if not entry:
                time.sleep(0.05)
        render.cleanup()

    except KeyboardInterrupt:
        render.cleanup()
        pass
