import os
import random
import socket
import threading
from tkinter import *
from PIL import Image, ImageTk, ImageFile

from RtpPacket import RtpPacket

ImageFile.LOAD_TRUNCATED_IMAGES = True
CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class ClienteGUI:

    # Initiation..
    def __init__(self, master, addr, port, server_ip, port_tcp):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.addr = addr
        self.port = int(port)
        self.rtspSeq = 0
        self.sessionId = random.randint(0, 10000)
        self.requestSent = -1
        self.teardownAcked = 0
        self.openRtpPort()
        self.frameNbr = 0
        self.server_ip = server_ip
        self.port_tcp = port_tcp
        self.tcpSocket = None

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

    def setupMovie(self):
        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpSocket.connect((self.server_ip, self.port_tcp))
        print("Sending")
        self.tcpSocket.sendall(b"Stream")

    def exitClient(self):
        if self.tcpSocket:
            self.tcpSocket.sendall(b"Stop")
            self.tcpSocket.close()
            os.remove(os.path.expanduser('~') + "/" + CACHE_FILE_NAME +
                      str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video
        self.master.destroy()  # Close the gui window

    def pauseMovie(self):
        self.playEvent.set()
        os.remove(os.path.expanduser('~') + "/" + CACHE_FILE_NAME + str(
            self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video

    def playMovie(self):
        """Play button handler."""
        # Create a new thread to listen for RTP packets
        threading.Thread(target=self.listenRtp).start()
        self.playEvent = threading.Event()
        self.playEvent.clear()

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                # Stop listening upon requesting PAUSE or TEARDOWN
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    if currFrameNbr > self.frameNbr:  # Discard the late packet
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
                if self.playEvent.is_set():
                    break
            except:

                self.rtpSocket.shutdown(socket.SHUT_RDWR)
                self.rtpSocket.close()
                break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = os.path.expanduser('~') + "/" + CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port
            self.rtpSocket.bind(("", self.port))
            print('\nBind \n')
        except:
            tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
