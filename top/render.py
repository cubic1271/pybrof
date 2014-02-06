__author__ = 'gc355804'

import curses
import datetime

class RenderState(object):
    HOME = 1

    TIMERS = 1
    THREADS = 2
    TABLES = 3

class Renderer(object):
    MAX_HIST_ENTRIES = 5

    def __init__(self, curses_init=True):
        self.history = []
        self._state = RenderState.HOME
        self.render = {
            RenderState.HOME: self.draw_home
        }
        # curses init
        if curses_init:
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)

    def _ralign(self, y, str, colors=None):
        if colors:
            self.stdscr.addstr(y, (self.width - len(str)) - 1, str, colors)
        else:
            self.stdscr.addstr(y, (self.width - len(str)) - 1, str)

    def _center(self, y, str, colors=None):
        if colors:
            self.stdscr.addstr(y, (self.width - len(str)) / 2, str, colors)
        else:
            self.stdscr.addstr(y, (self.width - len(str)) / 2, str)

    def draw_home(self, entry):
        last = None
        if len(self.history) > 0:
            last = self.history[-1]
        stdscr = self.stdscr
        screen_size = stdscr.getmaxyx()
        self.height = screen_size[0]
        self.width = screen_size[1]
        stdscr.move(0, 0)
        title = "BRO PROFILER"
        stdscr.addstr(0, 0, " " * self.width, curses.color_pair(1))
        self._center(0, title, curses.color_pair(1))
        self._ralign(0, str(datetime.datetime.fromtimestamp(entry.ts)), curses.color_pair(1))
        stdscr.addstr(2, 0, "Runtime: " + str(entry.time['real']) + "s")
        self._ralign(2, "CPU [" + str(entry.threads) + " threads]: " + str(entry.time['user']) + " user / " + str(entry.time['system']) + " sys")
        self._ralign(6, "Memory: " + str(entry.memory['total-adj'] / (1024 * 1024) ) + "M adjusted / " + str(entry.memory['total'] / (1024 * 1024)) + "M total")
        self._center(self.height - 1, "(q)uit | (t)oggle lists | (h)istory", curses.color_pair(3))
        if last:
            d_real = entry.time['real'] - last.time['real']
            d_user = entry.time['user'] - last.time['user']
            d_sys = entry.time['system'] - last.time['system']
            d_threads = entry.threads - last.threads
            d_adjusted = entry.memory['total-adj'] - last.memory['total-adj']
            d_total = entry.memory['total'] - last.memory['total']

            stdscr.addstr(3, 8, "+" + str(d_real) + "s")
            self._ralign(3, " [" + ("+" if d_threads >= 0 else "") + str(d_threads) + " threads]: +" + str(d_user) + " user / +" + str(d_sys) + " sys")
            self._ralign(4, " Utilization: " + str(100 * (int(1000 * (d_user / d_real)) / 1000.0)) + "% user / " + str(100 * (int(1000 * (d_sys / d_real)) / 1000.0)) + "% sys")
            self._ralign(7, " +" + str(d_adjusted / (1024 * 1024)) + "M adjusted / +" + str(d_total / (1024 * 1024)) + "M total")
        stdscr.move(0, 0)
        stdscr.refresh()

    def update(self, entry):
        self.render[self._state](entry)
        self.history.append(entry)
        if len(self.history) > Renderer.MAX_HIST_ENTRIES:
            del self.history[0]

    def cleanup(self):
        curses.nocbreak()
        curses.echo()
        curses.endwin()
