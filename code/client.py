import socket
import random
import struct
import threading
import ssl
import time

from hospital import Hospital

class Client:
   def __init__(self, port, name):
      self.port = port
      self.serve()
      self.max_bound = 10000
      threading.Thread(target=self.receive_shares, daemon=False).start() 
      self.name = name
      self.shares = []
      self.secret = random.randint(1, self.max_bound)
      print(f'{name} have secret {self.secret}')

   def generate_shares(self):
      newshares = []
      share1 = random.randint(1, self.max_bound)
      share2 = random.randint(1, self.max_bound)
      share3 = (self.secret - (share1 + share2)) % self.max_bound
      
      newshares.append(share1)
      newshares.append(share2)
      newshares.append(share3)

      return newshares
   
   def serve(self):
      server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      server_socket.bind(('localhost', self.port))
      server_socket.listen(5)


      context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
      context.load_cert_chain("server_cert.pem", "server_key.pem")
      self.tls_server = context.wrap_socket(server_socket)
         
   def connect(self, port):
      client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      client_socket.connect(('localhost', port))

      context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
      context.load_cert_chain("server_cert.pem", "server_key.pem")
      context.check_hostname = False
      context.verify_mode = ssl.CERT_NONE
      return context.wrap_socket(client_socket)

   def send_share(self, clients):
      shares = self.generate_shares()
      for i in range(len(clients)):
         if clients[i].name != self.name:
            client_socket = self.connect(clients[i].port)
            share = struct.pack("!i", shares[i])
            client_socket.send(share)
            client_socket.close()
         else: 
            self.shares.append(shares[i])
            #print(f"{self.name} received this share: {shares[i]}")
   
   def receive_shares(self):
      for _ in range(2):
        client_socket, _ = self.tls_server.accept()
        received_data = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            received_data += data
        
        share = struct.unpack("!i", received_data)[0]
        #print(f"{self.name} received this share: {share}")
        self.shares.append(share)
        client_socket.close()

      time.sleep(0.5)
      aggregation = sum(self.shares)%self.max_bound
      print(f"The aggregated values are {aggregation}")
      
      
      client_socket = self.connect(8000)
      aggregation_value = struct.pack("!i", aggregation)
      client_socket.send(aggregation_value)
      client_socket.close()



threading.Thread(target=Hospital, daemon=False).start() # Creates the hospital
alice = Client(8001, "Alice")
bob = Client(8002, "Bob")
charlie = Client(8003, "Charlie")

clients = [alice, bob, charlie]

print(f"The sum of secrets is = {(alice.secret + bob.secret + charlie.secret)%alice.max_bound}")
for client in clients:
   threading.Thread(target=client.send_share, args=(clients,), daemon=False).start()

