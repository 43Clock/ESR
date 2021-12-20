import atexit
import socket
import sys
import threading
import traceback
import re
from RtpPacket import RtpPacket
from VideoStream import VideoStream


class UDPWorker(threading.Thread):
    def __init__(self, event, videoStream, rtpPort, rtpSocket):
        threading.Thread.__init__(self)
        self.event = event
        self.videoStream = videoStream
        self.rtpPort = rtpPort
        self.rtpSocket = rtpSocket

    def run(self):
        """Send RTP packets over UDP."""
        while True:
            self.event.wait(0.05)

            # Stop sending if request is PAUSE or TEARDOWN
            if self.event.isSet():
                break

            data = self.videoStream.nextFrame()
            if data:
                frameNumber = self.videoStream.frameNbr()
                try:
                    address = socket.gethostbyname("127.0.0.1")
                    port = int(self.rtpPort)
                    packet = self.makeRtp(data, frameNumber)
                    self.rtpSocket.sendto(packet, (address, port))
                except:
                    print("Connection Error")
                    print('-' * 60)
                    traceback.print_exc(file=sys.stdout)
                    print('-' * 60)
        # Close the RTP socket
        self.rtpSocket.close()
        print("All done!")

    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26  # MJPEG type
        seqnum = frameNbr
        ssrc = 0

        rtpPacket = RtpPacket()

        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
        #print("Encoding RTP Packet: " + str(seqnum))

        return rtpPacket.getPacket()


class TCPWorker(threading.Thread):
    def __init__(self, tcpSocket:socket.socket, connection, clientAddr):
        threading.Thread.__init__(self)
        self.connection = connection
        self.client_ip = clientAddr
        self.tcpSocket = tcpSocket

    def run(self):
        while True:
            received = self.connection.recv(1024).decode("UTF-8")
            if received == "Stream":
                self.tcpSocket.sendall((bytes("Stream|" + self.client_ip,"utf-8")))
            else:
                self.tcpSocket.sendall((bytes("Stop|" + self.client_ip,"utf-8")))
                break

def check_if_ip(string):
    return re.match(r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}", string) is not None

class Servidor:

    def __init__(self):
        self.clientInfo = {}
        atexit.register(self.closeConnection)

    def closeConnection(self):
        self.clientInfo["tcpSocket2"].sendall(b"DisconnectStreaming")
        self.clientInfo["tcpSocket2"].close()

    def main(self):

        try:
            if check_if_ip(sys.argv[1]):
                self.clientInfo['Addr'] = sys.argv[1]
            else:
                print("IP inválido")
        except IndexError:
            print("IP não fornecido!")
            return
        try:
            # Get the media file name
            filename = sys.argv[2]
            print("Using provided video file ->  " + filename)
        except:
            print("[Usage: Servidor.py <videofile>]\n")
            filename = "movie.Mjpeg"
            print("Using default video file ->  " + filename)

        # videoStram
        self.clientInfo['videoStream'] = VideoStream(filename)
        # socket
        self.clientInfo['rtpPort'] = 8888

        # Create a new socket for RTP/UDP
        self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clientInfo["tcpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientInfo["tcpSocket"].bind(("", 9999))
        self.clientInfo["tcpSocket"].listen(0)
        self.clientInfo['event'] = threading.Event()
        self.clientInfo['worker'] = UDPWorker(self.clientInfo['event'], self.clientInfo['videoStream'],
                                              self.clientInfo['rtpPort'], self.clientInfo["rtpSocket"])
        self.clientInfo['worker'].start()
        self.clientInfo["tcpSocket2"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientInfo["tcpSocket2"].connect((self.clientInfo['Addr'], 8080))
        while True:
            connection, client_address = self.clientInfo["tcpSocket"].accept()
            worker = TCPWorker(self.clientInfo["tcpSocket2"], connection, client_address[0])
            worker.start()


if __name__ == "__main__":
    (Servidor()).main()
