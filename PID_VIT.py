import random
import math
import time
from threading import Thread

from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server

data = {'kp': .1, 'kd': .1, 'ki': .1,
        'desired': 0., 'pos': 0., 'vit': 0., 'pe': 0., 'ie': 0.}

global client

def setData(unused_addr, args, *message):
    global data
    print("[{0}]: {1}".format(args[0], message[0]))
    if args[0] in data:
        data[args[0]] = message[0]

def sendOsc(key, data):
    global client
    if abs(data) > 1e6 or math.isnan(data):
        data = 0.
    client.send_message("/" + key, data)

if __name__ == "__main__":
    global client
    client = udp_client.SimpleUDPClient('127.0.0.1', 10000)


    dispatcher = dispatcher.Dispatcher()
    for k in data.keys():
        dispatcher.map("/"+k, setData, k)

    server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', 10001), dispatcher)
    print("Serving on {}".format(server.server_address))

    thread = Thread(target=server.serve_forever, args=())
    thread.start()

    bias = 0
    start = time.time()
    previous = start
    frameDuration = 0.005
    fps = 0.
    frameCount = 0
    secondStarted = time.time()
    while True:
        frameCount += 1
        now = time.time()
        if now - secondStarted > .1:
            fps += frameCount / (now - secondStarted)
            fps *= .5
            client.send_message("/fps", fps)
            secondStarted = now
            frameCount = 0
        #elapsed = now - start
        #dt = now - previous

        desired, pos, vit, pe, ie = data['desired'], data['pos'], data['vit'], data['pe'], data['ie']
        kp, kd, ki = data['kp'], data['kd'], data['ki']

        error = (desired - vit) * 1.
        integral = ie + error * frameDuration
        derivative = (error - pe) * frameDuration

        newVit = kp * error * frameDuration + ki * integral - kd * derivative + bias
        pos += newVit * frameDuration

        data['pos'] = pos
        data['vit'] = newVit
        data['pe'] = error
        data['ie'] = integral

        for k in data.keys():
            sendOsc(k, data[k])

        frameActualDuration = time.time() - now
        timeLeftToSleep = frameDuration - frameActualDuration
        if timeLeftToSleep > 0:
            time.sleep(timeLeftToSleep)
        previous = now

