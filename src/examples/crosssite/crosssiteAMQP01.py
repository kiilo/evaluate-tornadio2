from os import path as op


import tornado.web
import tornado.httpserver

import tornadio2.router
import tornadio2.server
import tornadio2.conn
import tornado.platform.twisted
tornado.platform.twisted.install()


from tornadio2 import event
from amqp import AmqpFactory

ROOT = op.normpath(op.dirname(__file__))

class AmqpDB():
    DB_USER = 'db_login_name'
    DB_PASSWORD = 'db_login_passwd'
    DB_NAME = 'db_name'
    DB_HOST = 'localhost'
    
#AMQP_VHOST='/vcS3dDCWxcwoGaRKL2uYpvdcviv'
#AMQP_USER="uDp3GPbdahahEGBev8vaEM72xJs"
#AMQP_PASSWORD="cmDvdug946QGPZvFNmSko43CSn3"


    def getVhost(self, SessId):
        if (SessId == '001'):
            vhost = "/vcS3dDCWxcwoGaRKL2uYpvdcviv"
        elif(SessId == '002'):
            vhost = "v002"
        elif(SessId == '003'):
            vhost = "v003"
        else:
            vhost = ''
        return vhost
    
    def getUser(self, SessId):
        if (SessId == '001'):
            user = "uDp3GPbdahahEGBev8vaEM72xJs"
        elif(SessId == '002'):
            user = 'u002'
        elif(SessId == '003'):
            user = 'u003'
        else:
            user = ''
        return user

    def getPassw(self, SessId):
        if (SessId == '001'):
            passw = "cmDvdug946QGPZvFNmSko43CSn3"
        elif(SessId == '002'):
            passw = 'p002'
        elif(SessId == '003'):
            passw = 'p003'
        else:
            passw = ''
        return passw

class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the chatroom page"""
    def get(self):
        self.render('./amqp01.html')


class SocketIOHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('../socket.io.js')



class SocketConnection(tornadio2.conn.SocketConnection):
    # Class level variable
    participants = set()
    AMQP_HOST="localhost"
    AMQP_PORT=5672 
    # Get this file out of the txamqp distribution.
    AMQP_SPEC="specs/rabbitmq/amqp0-8.stripped.rabbitmq.xml"

    def on_open(self, info):
        self.send("Welcome from the server.")
        self.participants.add(self)

    def on_message(self, message):
        # Pong message back
        # loop over participants to deliver to each of them 
        #for p in self.participants:
            #p.send(message)
        pass

    def writeToSocket(self, msg):
        #self.send( amqpMsg )
        self.emit('amqpMsg', msg[3] + " " + msg[4] + " " + msg[5].body )

    def on_close(self):
        """dilute this client connection - Century Dictionary and Cyclopedia
           To render more liquid; make thin or more fluid, as by mixture of a fluid of less 
           with one of greater consistence; attenuate the strength or consistence of: often 
           used figuratively: as, to dilute a narrative with weak reflections.
           Hence To weaken, as spirit or an acid, by an admixture of water or other liquid, 
           which renders the spirit or acid less concentrated. """
        logging.log( logging.DEBUG, 'on_close:: close connection - client hanghup')
        self.participants.remove(self)
        self.amqpVhost = None
        self.amqpUser = None
        self.amqpPassw = None
        self.amqpFactory.clientConnectionLost(self.amqpFactory.connector, "client hangup") # .connectionLost( "client hangup")       #.close("client hangup")
        self.amqpFactory = None
        self = None # dilute into the void 
    
    @event('amqpMsg')    
    def amqpMsg(self, amqpMsg):
        #self.send('HERE within the message BULK: ' + amqpMsg)
        self.amqpFactory.send_message(exchange='messaging/', type='topic', routing_key='amqpMsg', msg=amqpMsg)
        
    @event('openAmqp')
    def openAmqp(self, amqpSessionId):
        logging.log(logging.DEBUG,'new client\n')
        amqpDB = AmqpDB()
        self.amqpVhost = amqpDB.getVhost(amqpSessionId)
        self.amqpUser  = amqpDB.getUser(amqpSessionId)
        self.amqpPassw = amqpDB.getPassw(amqpSessionId)
        
        #print(self.amqpVhost, self.amqpUser, self.amqpPassw)
        self.amqpFactory = AmqpFactory(host=self.AMQP_HOST, port=self.AMQP_PORT, vhost=self.amqpVhost, user=self.amqpUser, password=self.amqpPassw, spec_file=self.AMQP_SPEC)
        self.amqpFactory.read(exchange='messaging/', type="topic", queue="", routing_key='#', callback=self.writeToSocket)
        

# Create tornadio server
SocketRouter = tornadio2.router.TornadioRouter(SocketConnection)

# Create socket application
sock_app = tornado.web.Application(
    SocketRouter.urls,
    flash_policy_port = 843,
    flash_policy_file = op.join(ROOT, 'flashpolicy.xml'),
    socket_io_port = 8002
)

# Create HTTP application
http_app = tornado.web.Application(
    [(r"/", IndexHandler), (r"/socket.io.js", SocketIOHandler)]
)

if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    # Create http server on port 8001
    http_server = tornado.httpserver.HTTPServer(http_app)
    http_server.listen(8001)

    # Create tornadio server on port 8002, but don't start it yet
    tornadio2.server.SocketServer(sock_app, auto_start=False)

    # Start both servers
    tornado.ioloop.IOLoop.instance().start()
    