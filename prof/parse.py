import re
import time

__author__ = 'gc355804'

class ProfileLog(object):
    entry_expr = re.compile('^[0-9.]+ ---.*$')

    def __init__(self, path, block_iter = False):
        self.open(path)
        self.block_iter = block_iter

    def open(self, path):
        self.path = path
        self.fd = open(path)
        self.fd.readline()
        self.command = self.fd.readline()
        self.command = self.command.replace('0.000000 Command line:', '').replace('\n', '')
        self.fd.readline()
        # first two profile entries are junk data
        curr = self.fd.readline()
        while not ProfileLog.entry_expr.match(curr):
            curr = self.fd.readline()
        self.read()

    def read(self, primed=None):
        result = []
        curr = primed
        while not curr:
            curr = self.fd.readline()
            if not curr:
                time.sleep(0.1)
        while not ProfileLog.entry_expr.match(curr):
            result.append(curr)
            curr = None
            while not curr:
                curr = self.fd.readline()
                if not curr:
                    time.sleep(0.1)
        return ProfileEntry(result)

    ### Iterator definitions
    def __iter__(self):
        return self

    def next(self):
        curr = self.fd.readline()

        if not self.block_iter:
            if not curr:
                raise StopIteration
            else:
                return self.read(primed=curr)
        else:
            return self.read()

def parse_memory(entries, index, entry):
    target = entries[index].split(':', 1)
    entry.ts = float((target[0].split(' '))[0])
    target = target[1]
    target = target.split(' ')
    entry.memory = dict()
    entry.memory['total'] = long((target[1].replace('K', '').split('='))[1]) * 1024
    entry.memory['total-adj'] = long((target[2].replace('K', '').split('='))[1]) * 1024
    entry.memory['alloc'] = float(target[4].replace('K', '').replace('\n', '')) * 1024
    #print entry.memory
    return 1

def parse_runtimes(entries, index, entry):
    target = entries[index].split(':', 1)
    target = target[1]
    target = target.split(' ')
    entry.time = dict()
    entry.time['user'] = float((target[2].split('='))[1])
    entry.time['system'] = float((target[3].split('='))[1])
    entry.time['real'] = float((target[4].replace('\n', '').split('='))[1])
    #print entry.time
    return 1

def parse_conns(entries, index, entry):
    target = entries[index].split(':', 1)
    target = target[1]
    target = target.split(' ')
    entry.conns = dict()
    entry.conns['total'] = long((target[1].split('='))[1])
    entry.conns['current'] = (target[2].split('='))[1]
    entry.conns['ext'] = long((target[3].split('='))[1])
    entry.conns['mem'] = long((target[4].replace('K', '').split('='))[1]) * 1024
    entry.conns['avg'] = (target[5].split('='))[1]
    entry.conns['table'] = long((target[6].replace('K', '').split('='))[1]) * 1024
    entry.conns['connvals'] = long((target[7].replace('K', '').replace('\n', '').split('='))[1]) * 1024
    target = entries[index + 1].split(':', 1)
    target = target[1]
    target = target.split(' ')
    entry.conns['tcp'] = (target[1].split('='))[1]
    entry.conns['udp'] = (target[2].split('='))[1]
    entry.conns['icmp'] = (target[3].replace('\n', '').split('='))[1]
    #print entry.conns
    return 2

def parse_timers(entries, index, entry):
    target = entries[index].split(':', 1)
    target = target[1]
    target = target.split(' ')
    entry.timers = dict()
    entry.timers['current'] = long((target[1].split('='))[1])
    entry.timers['max'] = long((target[2].split('='))[1])
    entry.timers['mem'] = long((target[3].replace('K', '').split('='))[1]) * 1024
    entry.timers['lag'] = (target[4].replace('\n', '').split('='))[1]
    #print entry.timers
    return 1

# Note: timers are listed in order after triggers.  Acquire a list of all active timers ...
def parse_triggers(entries, index, entry):
    target = entries[index].split(':', 1)
    target = target[1]
    target = target.split(' ')
    entry.triggers = dict()
    entry.triggers['total'] = (target[1].split('='))[1]
    entry.triggers['pending'] = (target[2].replace('\n', '').split('='))[1]
    entry.timer_instances = dict()
    offset = index + 1
    while offset < len(entries) and not re.match('^.*:.*$', entries[offset]):
        entry.timer_instances[(entries[offset].split(' '))[9]] = ((entries[offset].split(' '))[11]).replace('\n', '')
        offset = offset + 1
    #print entry.triggers
    #print entry.timer_instances
    return offset - index

def parse_reassembly(entries, index, entry):
    target = entries[index].split(':', 1)
    target = target[1]
    target = target.split(' ')
    entry.reassembly = target[1].replace('\n', '')
    #print entry.reassembly
    return 1

class ThreadInstance(object):
    def __init__(self, desc):
        if not re.match('^.*Log::.*$', desc):
            self.name = '?'
            self.type = '?'
            return
        tmp = desc.split(' ')
        self.name = tmp[0].split('/')[0]
        self.type = tmp[0].split('/')[1]
        offset = 1
        while tmp[offset] == '':
            offset = offset + 1
        self.in_events = long(tmp[offset].split('=')[1])
        self.out_events = long(tmp[offset + 1].split('=')[1])
        self.pending_in = long(((tmp[offset + 2].split('/')[0]).split('='))[1])
        self.pending_out = long(tmp[offset + 2].split('/')[1])
        self.delivered_in = long(((tmp[offset + 5].split('/')[0]).split('='))[1])
        self.queued_in = long(tmp[offset + 5].split('/')[1])
        self.delivered_out = long(((tmp[offset + 6].split('/')[0]).split('='))[1])
        self.queued_out = long(tmp[offset + 6].replace(')', '').split('/')[1])

    @staticmethod
    def parse(entries, index, entry):
        target = entries[index].split(':', 1)
        target = target[1]
        target = target.split(' ')
        entry.threads = long((target[1].replace('\n', '').split('='))[1])
        entry.thread_instances = []
        offset = index + 1
        #print entries[offset].replace('\n', '').rsplit('   ', 1)
        while offset < len(entries) and re.match('^.*/.*$', entries[offset]):
            entry.thread_instances.append(ThreadInstance(entries[offset].replace('\n', '').rsplit('   ', 1)[1]))
            offset = offset + 1
        return offset - index

class ProfileEntry(object):
    TYPES = {
        'Memory':parse_memory,
        'Run-time':parse_runtimes,
        'Conns':parse_conns,
        'Timers':parse_timers,
        'Triggers':parse_triggers,
        'Threads':ThreadInstance.parse,
        'Total reassembler data':parse_reassembly
    }

    def __init__(self, text):
        index = 0
        while index < len(text):
            base = text[index].split(' ', 1)
            base = base[1]
            base = base.split(':', 1)
            base = base[0]

            if base in ProfileEntry.TYPES:
                result = ProfileEntry.TYPES[base](text, index, self)
                index = index + result
            else:
                #print "No such type: " + base
                index = index + 1

if __name__ == '__main__':
    log = ProfileLog('../prof.log')
    print log.command
    for entry in log:
        pass
