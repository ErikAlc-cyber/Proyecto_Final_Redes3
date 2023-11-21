import json
import networkx as nx
import matplotlib.pyplot as plt

# Leer el archivo JSON con la topología
with open('new-devices.json', 'r') as json_file:
    topology = json.load(json_file)

# Crear un grafo dirigido para representar la topología
G = nx.DiGraph()

# Agregar nodos y conexiones basados en la estructura JSON
for device, data in topology.items():
    G.add_node(device)  # Agregar dispositivo como nodo
    for subnet in data['Subredes']:
        for interface, details in subnet.items():
            ip_destino = details['ip']
            G.add_edge(device, ip_destino)  # Conectar dispositivo con la IP destino

# Layout personalizado para minimizar la superposición de nodos
pos = nx.spring_layout(G, k=0.3, iterations=50)

# Dibujar el grafo
plt.figure(figsize=(12, 10))
nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray', node_size=700, font_size=9)
plt.title("Network Topology from new-devices.json")
plt.show()