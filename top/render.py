__author__ = 'gc355804'

import curses
import datetime

class RenderState(object):
    HOME = 1

    TIMERS = 1
    THREADS = 2
    TABLES = 3

class Renderer(object):
    MAX_HIST_ENTRIES = 50

    def __init__(self, base=None, history=[]):
        self.finished = False
        self.advance = base.advance if base else True
        self.fetch = base.fetch if base else False
        self.history = history
        self.entry_index = base.entry_index if base else 0
        self._state = base._state if base else RenderState.HOME
        self.render = {
            RenderState.HOME: self.draw_home
        }
        self.input = {
            RenderState.HOME: self.input_home
        }
        # curses init
        if not base:
            self.stdscr = curses.initscr()
            self.stdscr.nodelay(1)
            curses.noecho()
            curses.cbreak()
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
        else:
            self.stdscr = base.stdscr

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

    def input_home(self, input):
        if input == curses.ERR:
            return
        if input == ord('q'):
            self.finished = True
        if input == ord('a'):
            self.advance = not self.advance
            self.entry_index = 0
        if input == ord('n'):
            self.entry_index += 1
        if input == ord('p'):
            self.entry_index -= 1
            self.advance = False
        if self.entry_index > 0:
            self.fetch = True
            self.entry_index = 0

    def draw_home(self, entry):
        last = None
        if len(self.history) > 0:
            last = self.history[-1]
        stdscr = self.stdscr
        stdscr.clear()
        screen_size = stdscr.getmaxyx()
        self.height = screen_size[0]
        self.width = screen_size[1]
        stdscr.move(0, 0)
        title = "BRO PROFILER"
        stdscr.addstr(0, 0, " " * self.width, curses.color_pair(1))
        if self.fetch:
            stdscr.addstr(0, 0, "(loading...)", curses.color_pair(1))
        elif self.advance:
            stdscr.addstr(0, 0, "(auto)", curses.color_pair(1))
        else:
            stdscr.addstr(0, 0, "(manual: " + str(self.entry_index) + ")", curses.color_pair(1))
        self._center(0, title, curses.color_pair(1))

        if not entry:
            self._center(self.height / 2, "Waiting on data.  Press the right arrow key / page down to get started ...")
            stdscr.move(0, 0)
            stdscr.refresh()
            return

        self._ralign(0, str(datetime.datetime.fromtimestamp(entry.ts)), curses.color_pair(1))
        stdscr.addstr(2, 0, "Runtime: " + str(entry.time['real']) + "s")
        self._ralign(2, "CPU [" + str(entry.threads) + " threads]: " + str(entry.time['user']) + " user / " + str(entry.time['system']) + " sys")
        self._ralign(5, "Memory: " + str(entry.memory['total-adj'] / (1024 * 1024) ) + "M adjusted / " + str(entry.memory['total'] / (1024 * 1024)) + "M total")
        self._center(self.height - 1, "(q)uit | (a)uto advance | (n)ext | (p)revious", curses.color_pair(3))
        stdscr.addstr(5, 0, "Active: " + str(entry.timers['current']) + " timers / " + str(entry.triggers['pending']) + " triggers")
        if last:
            d_real = entry.time['real'] - last.time['real']
            d_user = entry.time['user'] - last.time['user']
            d_sys = entry.time['system'] - last.time['system']
            d_threads = entry.threads - last.threads
            d_adjusted = entry.memory['total-adj'] - last.memory['total-adj']
            d_total = entry.memory['total'] - last.memory['total']
            d_timers = entry.timers['current'] - last.timers['current']
            d_triggers = entry.triggers['pending'] - last.triggers['pending']

            stdscr.addstr(6, 7, ("+" if d_timers >= 0 else "") + str(d_timers) + " timers / " + ("+" if d_triggers >= 0 else "") + str(d_triggers) + " triggers")
            self._ralign(3, " [" + ("+" if d_threads >= 0 else "") + str(d_threads) + " threads]: +" + str(d_user) + " user / +" + str(d_sys) + " sys")
            stdscr.addstr(3, 0, str(100 * (int(1000 * (d_user / d_real)) / 1000.0)) + "% user / " + str(100 * (int(1000 * (d_sys / d_real)) / 1000.0)) + "% sys")
            self._ralign(6, " +" + str(d_adjusted / (1024 * 1024)) + "M adjusted / +" + str(d_total / (1024 * 1024)) + "M total")
        stdscr.move(0, 0)
        stdscr.refresh()

    def update(self, entry):
        input = self.stdscr.getch()
        if input != curses.ERR:
            self.input[self._state](input)
        if self.entry_index < 0:
            if self.entry_index < (-(len(self.history) - 1)):
                self.entry_index = -(len(self.history) - 1)
            vrender = Renderer(base=self, history=self.history[:self.entry_index - 1])
            vrender.render[self._state](self.history[self.entry_index - 1])
        elif entry:
            self.render[self._state](entry)
            self.history.append(entry)
        elif len(self.history) > 0:
            tmp = self.history[-1]
            del self.history[-1]
            self.render[self._state](tmp)
            self.history.append(tmp)
        else:
            self.render[self._state](None)
        if len(self.history) > Renderer.MAX_HIST_ENTRIES:
            del self.history[0]

    def cleanup(self):
        curses.nocbreak()
        curses.echo()
        curses.endwin()
