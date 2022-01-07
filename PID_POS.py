import random
import time
from threading import Thread

from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server

data = {'kp': .1, 'kd': .1, 'ki': .1,
        'desired': 0., 'pos': 0., 'pe': 0., 'ie': 0.}


def setData(unused_addr, args, *message):
    global data
    print("[{0}]: {1}".format(args[0], message[0]))
    data[args[0]] = message[0]


if __name__ == "__main__":

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
    frameDuration = 0.01
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

        desired, pos, pe, ie = data['desired'], data['pos'], data['pe'], data['ie']
        kp, kd, ki = data['kp'], data['kd'], data['ki']

        error = desired - pos
        integral = ie + error * frameDuration
        derivative = (error - pe) * frameDuration

        newPos = kp * error + ki * integral + kd * derivative + bias

        data['pos'] = newPos
        data['pe'] = error
        data['ie'] = integral

        for k in data.keys():
            client.send_message("/"+k, data[k])

        frameActualDuration = time.time() - now
        timeLeftToSleep = frameDuration - frameActualDuration
        if timeLeftToSleep > 0:
            time.sleep(timeLeftToSleep)
        previous = now

