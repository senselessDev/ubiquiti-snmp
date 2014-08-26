import os
import serial 
import netsnmp
import time
import sys
from subprocess import PIPE, Popen
from threading  import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

p = Popen(['iperf', '-c', '192.168.1.3', '-i', '0.5', '-y', 'C', '-t', '9999'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
q = Queue()
t = Thread(target=enqueue_output, args=(p.stdout, q))
t.daemon = True
t.start()


txRateOID = netsnmp.Varbind('.1.3.6.1.4.1.14988.1.1.1.1.1.2')
rxRateOID = netsnmp.Varbind('.1.3.6.1.4.1.14988.1.1.1.1.1.3')
signalStrengthOID = netsnmp.Varbind('.1.3.6.1.4.1.14988.1.1.1.1.1.4')
channelOID = netsnmp.Varbind('.1.3.6.1.4.1.14988.1.1.1.1.1.7')

logfile = open('logfile.log', 'w')
ser = serial.Serial(port='/dev/tty.BT-GPS8JENTRO-SPPslave', baudrate=9600)

while True :
  line = ser.readline()
  if line.__len__() > 0:
    line += ser.readline()
    txRate =  netsnmp.snmpwalk(txRateOID,Version=1, DestHost='192.168.1.21', Community='public', UseNumeric=1)[0]
    rxRate = netsnmp.snmpwalk(rxRateOID,Version=1, DestHost='192.168.1.21', Community='public', UseNumeric=1)[0]
    signalStrength = netsnmp.snmpwalk(signalStrengthOID,Version=1, DestHost='192.168.1.21', Community='public', UseNumeric=1)[0]
    channel = netsnmp.snmpwalk(channelOID,Version=1, DestHost='192.168.1.21', Community='public', UseNumeric=1)[0]

    iperfLine = ''
    while True:
      try: iperfLine += q.get_nowait()
      except: break

    if iperfLine != '':
      iperfSplittedLine = iperfLine.split(',')
      transferredBytes = iperfSplittedLine[7]
      indexOfNewline = iperfSplittedLine[8].index('\n')
      bandwidth = iperfSplittedLine[8][0:indexOfNewline]
    else:
        transferredBytes = ''
        bandwidth = ''

    logfile.write('$GPUBI,' + txRate + ',' + rxRate + ',' + signalStrength + ',' + channel + ',' + transferredBytes + ',' + bandwidth + '*\n')
    logfile.write(line)
    print('$GPUBI,' + txRate + ',' + rxRate + ',' + signalStrength + ',' + channel + ',' + transferredBytes + ',' + bandwidth + '*\n')
    print(line)
