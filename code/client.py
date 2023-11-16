import socket
import random
import struct
import threading
import ssl

from hospital import Hospital

class Client:
   def __init__(self, port, name):
      self.port = port
      self.serve()
      threading.Thread(target=self.receive_shares, daemon=False).start() 
      self.name = name
      self.shares = []
      self.secret = random.randint(1, 1000)
      print(f'{name} have secret {self.secret}')

   def generate_shares(self):
      newshares = []
      share1 = random.randint(1, 1000)
      share2 = random.randint(1, 1000)
      share3 = self.secret - (share1 + share2)
      
      #share3 = (self.secret + 1000 - share1 - share2) % 1000
      #share3 = self.secret + 1000 - ((share1 + share2) % 1000)
      
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
            # print(f'{self.name} send {shares[i]} to {clients[i].name}')
            client_socket.close()
         else: 
            self.shares.append(shares[i])
   
   def receive_shares(self):
      # for _ in range(2):
      #    client_socket, addr = self.tls_server.accept()
      #    data = client_socket.recv(1024)
      #    share = struct.unpack("!i", data)[0]
      #    print(f"Received data length: {len(data)}")
      #    self.shares.append(share)
      #    # print(f'{self.name} receive {share} from {addr}')
      #    client_socket.close()

      for _ in range(2):
        client_socket, addr = self.tls_server.accept()
        received_data = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            received_data += data
        # print(f"Received data length: {len(received_data)}")
        share = struct.unpack("!i", received_data)[0]
        self.shares.append(share)
        client_socket.close()

      #aggregation = sum(self.shares)%1000
      aggregation = sum(self.shares)
      print(f"The aggregated values are {aggregation}")
      
      
      client_socket = self.connect(8000)
      aggregation_value = struct.pack("!i", aggregation)
      client_socket.send(aggregation_value)
      # print(f'{self.name} send {aggregation} to hospital')
      client_socket.close()

   

threading.Thread(target=Hospital, daemon=False).start() # Creates the hospital
alice = Client(8001, "Alice")
bob = Client(8002, "Bob")
charlie = Client(8003, "Charlie")

clients = [alice, bob, charlie]
print(f"The sum of secrets is = {alice.secret + bob.secret + charlie.secret}")
for client in clients:
   threading.Thread(target=client.send_share, args=(clients,), daemon=False).start()

