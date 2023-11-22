import socket
import struct
import ssl

class Hospital:
   def __init__(self):
      self.aggregations = []
      self.max_bound = 10000
      hospital_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      hospital_socket.bind(('localhost', 8000)) 
      hospital_socket.listen(3)  # Listen for up to 3 clients
      print("Hospital server is listening for clients...")

      context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
      context.load_cert_chain("server_cert.pem", "server_key.pem")
      tls_server = context.wrap_socket(hospital_socket)

      for _ in range(3):
         client_socket, addr = tls_server.accept()
         data = client_socket.recv(1024)
         value = struct.unpack("!i", data)[0]
         self.aggregations.append(value)
         client_socket.close()

      value = sum(self.aggregations)%self.max_bound
      print(f'The hospital received {value} from the clients')

