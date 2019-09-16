import serial
import re
import pylive
import argparse
import time
import os


initial_timestamp = None
initial_received = None
initial_sent = None
nodes_synchronised = None


# ----------------------------------------------------------------------------#
def parse_serial_pdr(pattern, serial_line):
    global initial_sent, initial_received
    if serial_line != '':
        m = re.search(pattern, str(serial_line))
        if m is not None:
            sent = int(m.group('sent'))
            received = int(m.group('received'))

            if initial_sent is None:
                initial_sent = sent
            if initial_received is None:
                initial_received = received

            if sent == 0 or received == 0:
                pdr = 0
            else:
                pdr = (received/sent) * 100

            return pdr


# ----------------------------------------------------------------------------#
def parse_serial_throughput(pattern, serial_line):
    global initial_timestamp, initial_received
    if serial_line != '':
        m = re.search(pattern, serial_line)
        if m is not None:
            received = int(m.group('received'))
            time = int(m.group('time'))/1000  # divide by 1000 for ms

            if initial_received is None:
                initial_received = received
            if initial_timestamp is None:
                initial_timestamp = time

            delta_time = time - initial_timestamp
            delta_received = received - initial_received
            if delta_time != 0:
                return delta_received/(delta_time/1000)  # divide by 1000 for seconds
            else:
                return 0


# ----------------------------------------------------------------------------#
def parse_serial_sync(pattern, line, n_nodes=100):
    global nodes_synchronised
    if nodes_synchronised is None:
        nodes_synchronised = [0] * n_nodes
    if line != '':
        m = re.search(pattern, line)
        if m is not None:
            node = int(m.group('sync'))
            # ts = int(m.group('time'))
            nodes_synchronised[node] = 1
            n_sync = nodes_synchronised.count(1)
            return (n_sync/n_nodes) * 100
        else:
            return None


# ----------------------------------------------------------------------------#
def follow(thefile):
    thefile.seek(0, os.SEEK_END)  # End-of-file
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)  # Sleep briefly
            continue
        yield line


# ----------------------------------------------------------------------------#
class Interface:
    """Interface class."""
    _registry = []

    def __init__(self, name, **kwargs):
        # self.type = type

        self.log = kwargs['log'] if 'log' in kwargs else None
        self.ser = kwargs['ser'] if 'ser' in kwargs else None

        if self.log is not None:
            self.logfile = open(self.log, 'r')
            self.loglines = follow(self.logfile)

        self._registry.append(self)
        self.name = name

    def readline(self):
        if self.ser is not None:
            line = self.ser.readline()
            print(line)
            return line
        if self.log is not None:
            return self.logfile.readline()


# ----------------------------------------------------------------------------#
if __name__ == "__main__":
    # Regex
    re_pdr = '^.*PDR:\s*(?P<received>\d+)\/(?P<sent>\d+)\s(?P<time>\d+).*$'
    re_throughput = '^.*PDR:\s*(?P<received>\d+)\/(?P<sent>\d+)\s(?P<time>\d+).*$'
    re_sync = '^\s*(?P<time>\d+).*A:(?P<sync>\d+).*$'

    # Cmd line args
    ap = argparse.ArgumentParser(prog='contiki-serial', description='Contiki serial connector')
    ap.add_argument('--ports', required=False, help='Serial ports')
    ap.add_argument('--log',   required=False, help='Logfile')
    ap.add_argument('--p',     required=False, default=0, help='PDR')
    ap.add_argument('--t',     required=False, default=0, help='Throughput')
    ap.add_argument('--s',     required=False, default=0, help='Syncrhronisation')
    ap.add_argument('--all',   required=False, default=0, help='all')
    args = ap.parse_args()

    # Get interfaces
    if args.ports:
        for port in args.ports.split():
            inf = Interface(port, ser=serial.Serial(port, 115200, rtscts=True, dsrdtr=True))

    if args.log:
        inf = Interface(args.log, log=args.log)
    if args.all:
        args.p = args.t = args.s = 1
    if args.p:
        pylive.PyLive(re_pdr, parse_serial_pdr,
                      'PDR: {0!s:.2s}%',
                      'PDR', 'Time', 'PDR (%)')
    if args.t:
        pylive.PyLive(re_throughput, parse_serial_throughput,
                      'Throughput: {0!s:.2s} packets per second',
                      'Throughput', 'Time', 'Throughput (packets per second)')
    if args.s:
        pylive.PyLive(re_sync, parse_serial_sync,
                      'Sync: {0!s:.2s}%',
                      'Synchronisation', 'Time', 'Nodes Synchronised (%)')

    for inf in Interface._registry:
        for pyl in pylive.PyLive._registry:
            pyl.add_series(inf.name)


    pylive.start()


    while True:
        # Get input from each interface
        for inf in Interface._registry:
            for pyl in pylive.PyLive._registry:
                # follow(inf.logfile)
                line = inf.readline()
                if line != '':
                    if pyl.update(inf.name, str(line)):
                        print(inf.name, end=' ')
                        print(pyl)
        pylive.tick()
