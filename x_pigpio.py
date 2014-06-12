#!/usr/bin/env python3

#*** WARNING ************************************************
#*                                                          *
#* All the tests make extensive use of gpio 4 (pin P1-7).   *
#* Ensure that either nothing or just a LED is connected to *
#* gpio 4 before running any of the tests.                  *
#************************************************************

import sys
import time
import codecs
import struct

import pigpio

GPIO=4

def STRCMP(r, s):
   if r != codecs.latin_1_encode(s)[0]:
      print(r, codecs.latin_1_encode(s)[0])
      return 0
   else:
      return 1

def CHECK(t, st, got, expect, pc, desc):
   if got >= (((1E2-pc)*expect)/1E2) and got <= (((1E2+pc)*expect)/1E2):
      print("TEST {:2d}.{:<2d} PASS ({}: {:d})".format(t, st, desc, expect))
   else:
      print("TEST {:2d}.{:<2d} FAILED got {:d} ({}: {:d})".
         format(t, st, got, desc, expect))

def t0():

   print("Version.")

   print("pigpio version {}.".format(pi.get_pigpio_version()))

   print("Hardware revision {}.".format(pi.get_hardware_revision()))

def t1():

   print("Mode/PUD/read/write tests.")

   pi.set_mode(GPIO, pigpio.INPUT)
   v = pi.get_mode(GPIO)
   CHECK(1, 1, v, 0, 0, "set mode, get mode")

   pi.set_pull_up_down(GPIO, pigpio.PUD_UP)
   v = pi.read(GPIO)
   CHECK(1, 2, v, 1, 0, "set pull up down, read")

   pi.set_pull_up_down(GPIO, pigpio.PUD_DOWN)
   v = pi.read(GPIO)
   CHECK(1, 3, v, 0, 0, "set pull up down, read")

   pi.write(GPIO, pigpio.LOW)
   v = pi.get_mode(GPIO)
   CHECK(1, 4, v, 1, 0, "write, get mode")

   v = pi.read(GPIO)
   CHECK(1, 5, v, 0, 0, "read")

   pi.write(GPIO, pigpio.HIGH)
   v = pi.read(GPIO)
   CHECK(1, 6, v, 1, 0, "write, read")

t2_count=0

def t2cbf(gpio, level, tick):
   global t2_count
   t2_count += 1

def t2():

   global t2_count

   print("PWM dutycycle/range/frequency tests.")

   pi.set_PWM_range(GPIO, 255)
   pi.set_PWM_frequency(GPIO,0)
   f = pi.get_PWM_frequency(GPIO)
   CHECK(2, 1, f, 10, 0, "set PWM range, set/get PWM frequency")

   t2cb = pi.callback(GPIO, pigpio.EITHER_EDGE, t2cbf)

   pi.set_PWM_dutycycle(GPIO, 0)
   time.sleep(0.5) # allow old notifications to flush
   oc = t2_count
   time.sleep(2)
   f = t2_count - oc
   CHECK(2, 2, f, 0, 0, "set PWM dutycycle, callback")

   pi.set_PWM_dutycycle(GPIO, 128)
   time.sleep(1)
   oc = t2_count
   time.sleep(2)
   f = t2_count - oc
   CHECK(2, 3, f, 40, 5, "set PWM dutycycle, callback")

   pi.set_PWM_frequency(GPIO,100)
   f = pi.get_PWM_frequency(GPIO)
   CHECK(2, 4, f, 100, 0, "set/get PWM frequency")

   time.sleep(1)
   oc = t2_count
   time.sleep(2)
   f = t2_count - oc
   CHECK(2, 5, f, 400, 1, "callback")

   pi.set_PWM_frequency(GPIO,1000)
   f = pi.get_PWM_frequency(GPIO)
   CHECK(2, 6, f, 1000, 0, "set/get PWM frequency")

   time.sleep(1)
   oc = t2_count
   time.sleep(2)
   f = t2_count - oc
   CHECK(2, 7, f, 4000, 1, "callback")

   r = pi.get_PWM_range(GPIO)
   CHECK(2, 8, r, 255, 0, "get PWM range")

   rr = pi.get_PWM_real_range(GPIO)
   CHECK(2, 9, rr, 200, 0, "get PWM real range")

   pi.set_PWM_range(GPIO, 2000)
   r = pi.get_PWM_range(GPIO)
   CHECK(2, 10, r, 2000, 0, "set/get PWM range")

   rr = pi.get_PWM_real_range(GPIO)
   CHECK(2, 11, rr, 200, 0, "get PWM real range")

   pi.set_PWM_dutycycle(GPIO, 0)

t3_reset=True
t3_count=0
t3_tick=0
t3_on=0.0
t3_off=0.0

def t3cbf(gpio, level, tick):
   global t3_reset, t3_count, t3_tick, t3_on, t3_off

   if t3_reset:
      t3_count = 0
      t3_on = 0.0
      t3_off = 0.0
      t3_reset = False
   else:
      td = pigpio.tickDiff(t3_tick, tick)

      if level == 0:
         t3_on += td
      else:
         t3_off += td

   t3_count += 1
   t3_tick = tick

def t3():

   global t3_reset, t3_count, t3_on, t3_off

   pw=[500.0, 1500.0, 2500.0]
   dc=[0.2, 0.4, 0.6, 0.8]

   print("PWM/Servo pulse accuracy tests.")

   t3cb = pi.callback(GPIO, pigpio.EITHER_EDGE, t3cbf)

   t = 0
   for x in pw:
      t += 1
      pi.set_servo_pulsewidth(GPIO, x)
      time.sleep(1)
      t3_reset = True
      time.sleep(4)
      c = t3_count
      on = t3_on
      off = t3_off
      CHECK(3, t, int((1E3*(on+off))/on), int(2E7/x), 1, "set servo pulsewidth")


   pi.set_servo_pulsewidth(GPIO, 0)
   pi.set_PWM_frequency(GPIO, 1000)
   f = pi.get_PWM_frequency(GPIO)
   CHECK(3, 4, f, 1000, 0, "set/get PWM frequency")

   rr = pi.set_PWM_range(GPIO, 100)
   CHECK(3, 5, rr, 200, 0, "set PWM range")

   t = 5
   for x in dc:
      t += 1
      pi.set_PWM_dutycycle(GPIO, x*100)
      time.sleep(1)
      t3_reset = True
      time.sleep(2)
      c = t3_count
      on = t3_on
      off = t3_off
      CHECK(3, t, int((1E3*on)/(on+off)), int(1E3*x), 1, "set PWM dutycycle")

   pi.set_PWM_dutycycle(GPIO, 0)

def t4():

   print("Pipe notification tests.")

   pi.set_PWM_frequency(GPIO, 0)
   pi.set_PWM_dutycycle(GPIO, 0)
   pi.set_PWM_range(GPIO, 100)

   h = pi.notify_open()
   e = pi.notify_begin(h, (1<<4))
   CHECK(4, 1, e, 0, 0, "notify open/begin")

   time.sleep(1)

   try:
      f = open("/dev/pigpio"+ str(h), "rb")
   except IOError:
      f = None

   pi.set_PWM_dutycycle(GPIO, 50)
   time.sleep(4)
   pi.set_PWM_dutycycle(GPIO, 0)

   e = pi.notify_pause(h)
   CHECK(4, 2, e, 0, 0, "notify pause")

   e = pi.notify_close(h)
   CHECK(4, 3, e, 0, 0, "notify close")

   if f is not None:

      n = 0
      s = 0

      seq_ok = 1
      toggle_ok = 1

      while True:

         chunk = f.read(12)

         if len(chunk) == 12:

            S, fl, t, v = struct.unpack('HHII', chunk)
            if s != S:
               seq_ok = 0

            L = v & (1<<4)

            if n:
               if l != L:
                  toggle_ok = 0

            if L:
               l = 0
            else:
               l = (1<<4)
           
            s += 1
            n += 1

         else:
            break

      f.close()

      CHECK(4, 4, seq_ok, 1, 0, "sequence numbers ok")
      CHECK(4, 5, toggle_ok, 1, 0, "gpio toggled ok")
      CHECK(4, 6, n, 80, 10, "number of notifications")

   else:

      CHECK(4, 4, 0, 0, 0, "NOT APPLICABLE")
      CHECK(4, 5, 0, 0, 0, "NOT APPLICABLE")
      CHECK(4, 6, 0, 0, 0, "NOT APPLICABLE")

t5_count = 0

def t5cbf(gpio, level, tick):
   global t5_count
   t5_count += 1

def t5():
   global t5_count

   BAUD=4800

   TEXT="""
Now is the winter of our discontent
Made glorious summer by this sun of York;
And all the clouds that lour'd upon our house
In the deep bosom of the ocean buried.
Now are our brows bound with victorious wreaths;
Our bruised arms hung up for monuments;
Our stern alarums changed to merry meetings,
Our dreadful marches to delightful measures.
Grim-visaged war hath smooth'd his wrinkled front;
And now, instead of mounting barded steeds
To fright the souls of fearful adversaries,
He capers nimbly in a lady's chamber
To the lascivious pleasing of a lute.
"""

   print("Waveforms & bit bang serial read/write tests.")

   t5cb = pi.callback(GPIO, pigpio.FALLING_EDGE, t5cbf)

   pi.set_mode(GPIO, pigpio.OUTPUT)

   e = pi.wave_clear()
   CHECK(5, 1, e, 0, 0, "callback, set mode, wave clear")

   wf = []

   wf.append(pigpio.pulse(1<<GPIO, 0,  10000))
   wf.append(pigpio.pulse(0, 1<<GPIO,  30000))
   wf.append(pigpio.pulse(1<<GPIO, 0,  60000))
   wf.append(pigpio.pulse(0, 1<<GPIO, 100000))

   e = pi.wave_add_generic(wf)
   CHECK(5, 2, e, 4, 0, "pulse, wave add generic")

   e = pi.wave_tx_repeat()
   CHECK(5, 3, e, 9, 0, "wave tx repeat")

   oc = t5_count
   time.sleep(5)
   c = t5_count - oc
   CHECK(5, 4, c, 50, 1, "callback")

   e = pi.wave_tx_stop()
   CHECK(5, 5, e, 0, 0, "wave tx stop")

   e = pi.bb_serial_read_open(GPIO, BAUD)
   CHECK(5, 6, e, 0, 0, "serial read open")

   pi.wave_clear()
   e = pi.wave_add_serial(GPIO, BAUD, 5000000, TEXT)
   CHECK(5, 7, e, 3405, 0, "wave clear, wave add serial")

   e = pi.wave_tx_start()
   CHECK(5, 8, e, 6811, 0, "wave tx start")

   oc = t5_count
   time.sleep(3)
   c = t5_count - oc
   CHECK(5, 9, c, 0, 0, "callback")

   oc = t5_count
   while pi.wave_tx_busy():
      time.sleep(0.1)
   time.sleep(0.1)
   c = t5_count - oc
   CHECK(5, 10, c, 1702, 0, "wave tx busy, callback")

   c, text = pi.bb_serial_read(GPIO)
   CHECK(5, 11, STRCMP(text, TEXT), True, 0, "wave tx busy, serial read");

   e = pi.bb_serial_read_close(GPIO)
   CHECK(5, 12, e, 0, 0, "serial read close")

   c = pi.wave_get_micros()
   CHECK(5, 13, c, 6158704, 0, "wave get micros")

   CHECK(5, 14, 0, 0, 0, "NOT APPLICABLE")

   c = pi.wave_get_max_micros()
   CHECK(5, 15, c, 1800000000, 0, "wave get max micros")

   c = pi.wave_get_pulses()
   CHECK(5, 16, c, 3405, 0, "wave get pulses")

   CHECK(5, 17, 0, 0, 0, "NOT APPLICABLE")

   c = pi.wave_get_max_pulses()
   CHECK(5, 18, c, 12000, 0, "wave get max pulses")

   c = pi.wave_get_cbs()
   CHECK(5, 19, c, 6810, 0, "wave get cbs")

   CHECK(5, 20, 0, 0, 0, "NOT APPLICABLE")

   c = pi.wave_get_max_cbs()
   CHECK(5, 21, c, 25016, 0, "wave get max cbs")

   e = pi.wave_clear()
   CHECK(5, 22, e, 0, 0, "wave clear")

   e = pi.wave_add_generic(wf)
   CHECK(5, 23, e, 4, 0, "pulse, wave add generic")

   w1 = pi.wave_create()
   CHECK(5, 24, w1, 0, 0, "wave create")

   e = pi.wave_send_repeat(w1)
   CHECK(5, 25, e, 9, 0, "wave send repeat")

   oc = t5_count
   time.sleep(5)
   c = t5_count - oc
   CHECK(5, 26, c, 50, 1, "callback")

   e = pi.wave_tx_stop()
   CHECK(5, 27, e, 0, 0, "wave tx stop")

   e = pi.wave_add_serial(GPIO, BAUD, 5000000, TEXT)
   CHECK(5, 28, e, 3405, 0, "wave add serial")

   w2 = pi.wave_create()
   CHECK(5, 29, w2, 1, 0, "wave create")

   e = pi.wave_send_once(w2)
   CHECK(5, 30, e, 6811, 0, "wave send once")

   oc = t5_count
   time.sleep(3)
   c = t5_count - oc
   CHECK(5, 31, c, 0, 0, "callback")

   oc = t5_count
   while pi.wave_tx_busy():
      time.sleep(0.1)
   time.sleep(0.1)
   c = t5_count - oc
   CHECK(5, 32, c, 1702, 0, "wave tx busy, callback")

   e = pi.wave_delete(0)
   CHECK(5, 33, e, 0, 0, "wave delete")

t6_count=0
t6_on=0
t6_on_tick=None

def t6cbf(gpio, level, tick):
   global t6_count, t6_on, t6_on_tick
   if level == 1:
      t6_on_tick = tick
      t6_count += 1
   else:
      if t6_on_tick is not None:
         t6_on += pigpio.tickDiff(t6_on_tick, tick)

def t6():
   global t6_count, t6_on

   print("Trigger tests.")

   pi.write(GPIO, pigpio.LOW)

   tp = 0

   t6cb = pi.callback(GPIO, pigpio.EITHER_EDGE, t6cbf)

   for t in range(5):
      time.sleep(0.1)
      p = 10 + (t*10)
      tp += p;
      pi.gpio_trigger(GPIO, p, 1)

   time.sleep(0.5)

   CHECK(6, 1, t6_count, 5, 0, "gpio trigger count")

   CHECK(6, 2, t6_on, tp, 25, "gpio trigger pulse length")

t7_count=0

def t7cbf(gpio, level, tick):
   global t7_count
   if level == pigpio.TIMEOUT:
      t7_count += 1

def t7():
   global t7_count

   print("Watchdog tests.")

   # type of edge shouldn't matter for watchdogs
   t7cb = pi.callback(GPIO, pigpio.FALLING_EDGE, t7cbf)

   pi.set_watchdog(GPIO, 10) # 10 ms, 100 per second
   time.sleep(0.5)
   oc = t7_count
   time.sleep(2)
   c = t7_count - oc
   CHECK(7, 1, c, 200, 1, "set watchdog on count")

   pi.set_watchdog(GPIO, 0) # 0 switches watchdog off
   time.sleep(0.5)
   oc = t7_count
   time.sleep(2)
   c = t7_count - oc
   CHECK(7, 2, c, 0, 1, "set watchdog off count")

def t8():
   print("Bank read/write tests.")

   pi.write(GPIO, 0)
   v = pi.read_bank_1() & (1<<GPIO)
   CHECK(8, 1, v, 0, 0, "read bank 1")

   pi.write(GPIO, 1)
   v = pi.read_bank_1() & (1<<GPIO)
   CHECK(8, 2, v, (1<<GPIO), 0, "read bank 1")

   pi.clear_bank_1(1<<GPIO)
   v = pi.read(GPIO)
   CHECK(8, 3, v, 0, 0, "clear bank 1")

   pi.set_bank_1(1<<GPIO)
   v = pi.read(GPIO)
   CHECK(8, 4, v, 1, 0, "set bank 1")

   t = 0
   v = (1<<16)
   for i in range(100):
      if pi.read_bank_2() & v:
         t += 1
   CHECK(8, 5, t, 60, 75, "read bank 2")

   v = pi.clear_bank_2(0)
   CHECK(8, 6, v, 0, 0, "clear bank 2")

   pigpio.exceptions = False
   v = pi.clear_bank_2(0xffffff)
   pigpio.exceptions = True
   CHECK(8, 7, v, pigpio.PI_SOME_PERMITTED, 0, "clear bank 2")

   v = pi.set_bank_2(0)
   CHECK(8, 8, v, 0, 0, "set bank 2")

   pigpio.exceptions = False
   v = pi.set_bank_2(0xffffff)
   pigpio.exceptions = True
   CHECK(8, 9, v, pigpio.PI_SOME_PERMITTED, 0, "set bank 2")

def t9():
   print("Script store/run/status/stop/delete tests.")

   pi.write(GPIO, 0) # need known state

   # 100 loops per second
   # p0 number of loops
   # p1 GPIO
   script="""
   lda p0
   sta v0
   tag 0
   w p1 1
   mils 5
   w p1 0
   mils 5
   dcr v0
   lda v0
   sta p9
   jp 0"""

   t9cb = pi.callback(GPIO)

   s = pi.store_script(script)
   oc = t9cb.tally()
   pi.run_script(s, [99, GPIO])
   time.sleep(2)
   c = t9cb.tally() - oc
   CHECK(9, 1, c, 100, 0, "store/run script")

   oc = t9cb.tally()
   pi.run_script(s, [200, GPIO])
   while True:
      e, p = pi.script_status(s)
      if e != pigpio.PI_SCRIPT_RUNNING:
         break
      time.sleep(0.5)
   c = t9cb.tally() - oc
   time.sleep(0.1)
   CHECK(9, 2, c, 201, 0, "run script/script status")

   oc = t9cb.tally()
   pi.run_script(s, [2000, GPIO])
   while True:
      e, p = pi.script_status(s)
      if e != pigpio.PI_SCRIPT_RUNNING:
         break
      if p[9] < 1900:
         pi.stop_script(s)
      time.sleep(0.1)
   c = t9cb.tally() - oc
   time.sleep(0.1)
   CHECK(9, 3, c, 110, 10, "run/stop script/script status")

   e = pi.delete_script(s)
   CHECK(9, 4, e, 0, 0, "delete script")

def ta():
   print("Serial link tests.")

   # this test needs RXD and TXD to be connected

   h = pi.serial_open("/dev/ttyAMA0", 57600)
   CHECK(10, 1, h, 0, 0, "serial open")

   (b, s) = pi.serial_read(h, 1000) # flush buffer

   b = pi.serial_data_available(h)
   CHECK(10, 2, b, 0, 0, "serial data available")

   TEXT = """
To be, or not to be, that is the question-
Whether 'tis Nobler in the mind to suffer
The Slings and Arrows of outrageous Fortune,
Or to take Arms against a Sea of troubles,
"""
   e = pi.serial_write(h, TEXT)
   CHECK(10, 3, e, 0, 0, "serial write")

   e = pi.serial_write_byte(h, 0xAA)
   e = pi.serial_write_byte(h, 0x55)
   e = pi.serial_write_byte(h, 0x00)
   e = pi.serial_write_byte(h, 0xFF)

   CHECK(10, 4, e, 0, 0, "serial write byte")

   time.sleep(0.1) # allow time for transmission

   b = pi.serial_data_available(h)
   CHECK(10, 5, b, len(TEXT)+4, 0, "serial data available")

   (b, text) = pi.serial_read(h, len(TEXT))
   CHECK(10, 6, b, len(TEXT), 0, "serial read")
   CHECK(10, 7, STRCMP(text, TEXT), True, 0, "serial read")

   b = pi.serial_read_byte(h)
   CHECK(10, 8, b, 0xAA, 0, "serial read byte")

   b = pi.serial_read_byte(h)
   CHECK(10, 9, b, 0x55, 0, "serial read byte")

   b = pi.serial_read_byte(h)
   CHECK(10, 10, b, 0x00, 0, "serial read byte")

   b = pi.serial_read_byte(h)
   CHECK(10, 11, b, 0xFF, 0, "serial read byte")

   b = pi.serial_data_available(h)
   CHECK(10, 12, b, 0, 0, "serial data available")

   e = pi.serial_close(h)
   CHECK(10, 13, e, 0, 0, "serial close")

def tb():
   print("SMBus / I2C tests.")

   # this test requires an ADXL345 on I2C bus 1 addr 0x53

   h = pi.i2c_open(1, 0x53)
   CHECK(11, 1, h, 0, 0, "i2c open")

   e = pi.i2c_write_device(h, "\x00") # move to known register
   CHECK(11, 2, e, 0, 0, "i2c write device")

   (b, d)  = pi.i2c_read_device(h, 1)
   CHECK(11, 3, b, 1, 0, "i2c read device")
   CHECK(11, 4, ord(d), 0xE5, 0, "i2c read device")

   b = pi.i2c_read_byte(h)
   CHECK(11, 5, b, 0xE5, 0, "i2c read byte")

   b = pi.i2c_read_byte_data(h, 0)
   CHECK(11, 6, b, 0xE5, 0, "i2c read byte data")

   b = pi.i2c_read_byte_data(h, 48)
   CHECK(11, 7, b, 2, 0, "i2c read byte data")

   exp = "[aB\x08cD\xAAgHj\xFD]"

   e = pi.i2c_write_device(h, '\x1D' + exp)
   CHECK(11, 8, e, 0, 0, "i2c write device")

   e = pi.i2c_write_device(h, '\x1D')
   (b, d)  = pi.i2c_read_device(h, 12)
   CHECK(11, 9, b, 12, 0, "i2c read device")
   CHECK(11, 10, STRCMP(d, exp), True, 0, "i2c read device")

   e = pi.i2c_write_byte_data(h, 0x1d, 0xAA)
   CHECK(11, 11, e, 0, 0, "i2c write byte data")

   b = pi.i2c_read_byte_data(h, 0x1d)
   CHECK(11, 12, b, 0xAA, 0, "i2c read byte data")

   e = pi.i2c_write_byte_data(h, 0x1d, 0x55)
   CHECK(11, 13, e, 0, 0, "i2c write byte data")

   b = pi.i2c_read_byte_data(h, 0x1d)
   CHECK(11, 14, b, 0x55, 0, "i2c read byte data")

   exps = b"[1234567890#]"
   exp  =  "[1234567890#]"

   e = pi.i2c_write_block_data(h, 0x1C, exps)
   CHECK(11, 15, e, 0, 0, "i2c write block data")

   e = pi.i2c_write_device(h, '\x1D')
   (b, d)  = pi.i2c_read_device(h, 13)
   CHECK(11, 16, b, 13, 0, "i2c read device")
   CHECK(11, 17, STRCMP(d, exp), True, 0, "i2c read device")

   (b, d)  = pi.i2c_read_i2c_block_data(h, 0x1D, 13)
   CHECK(11, 18, b, 13, 0, "i2c read i2c block data")
   CHECK(11, 19, STRCMP(d, exp), True, 0, "i2c read i2c block data")

   expl = [0x01, 0x05, 0x06, 0x07, 0x09, 0x1B, 0x99, 0xAA, 0xBB, 0xCC]
   exp = "\x01\x05\x06\x07\x09\x1B\x99\xAA\xBB\xCC"

   e = pi.i2c_write_i2c_block_data(h, 0x1D, expl)
   CHECK(11, 20, e, 0, 0, "i2c write i2c block data")

   (b, d)  = pi.i2c_read_i2c_block_data(h, 0x1D, 10)
   CHECK(11, 21, b, 10, 0, "i2c read i2c block data")
   CHECK(11, 22, STRCMP(d, exp), True, 0, "i2c read i2c block data")

   e = pi.i2c_close(h)
   CHECK(11, 23, e, 0, 0, "i2c close")

def tca(b, d):
   if b == 3:
      c1 = d[1] & 0x0F
      c2 = d[2]
      time.sleep(1.0)
      print((c1*256)+c2)

def tc():
   print("SPI tests.")

   # this test requires a MCP3202 on SPI channel 1

   h = pi.spi_open(1, 50000)
   CHECK(12, 1, h, 0, 0, "spi open")

   (b, d) = pi.spi_xfer(h, [1,128,0])
   CHECK(12, 2, b, 3, 0, "spi xfer")
   tca(b, d)

   (b, d) = pi.spi_xfer(h, "\x01\x80\x00")
   CHECK(12, 2, b, 3, 0, "spi xfer")
   tca(b, d)

   (b, d) = pi.spi_xfer(h, b"\x01\x80\x00")
   CHECK(12, 2, b, 3, 0, "spi xfer")
   tca(b, d)

   (b, d) = pi.spi_xfer(h, '\x01\x80\x00')
   CHECK(12, 2, b, 3, 0, "spi xfer")
   tca(b, d)

   (b, d) = pi.spi_xfer(h, b'\x01\x80\x00')
   CHECK(12, 2, b, 3, 0, "spi xfer")
   tca(b, d)

   e = pi.spi_close(h)
   CHECK(12, 99, e, 0, 0, "spi close")

if len(sys.argv) > 1:
   tests = ""
   for C in sys.argv[1]:
      c = C.lower()
      if c not in tests:
         tests += c

else:
   tests = "0123456789"

pi = pigpio.pi()

if pi.connected:
   print("Connected to pigpio daemon.")

   if '0' in tests: t0()
   if '1' in tests: t1()
   if '2' in tests: t2()
   if '3' in tests: t3()
   if '4' in tests: t4()
   if '5' in tests: t5()
   if '6' in tests: t6()
   if '7' in tests: t7()
   if '8' in tests: t8()
   if '9' in tests: t9()
   if 'a' in tests: ta()
   if 'b' in tests: tb()
   if 'c' in tests: tc()

pi.stop()

