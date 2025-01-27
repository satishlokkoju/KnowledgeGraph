from flask import Flask, render_template, jsonify, request
import networkx as nx
import json
import os
from datetime import datetime

app = Flask(__name__)

# In-memory graph storage
graph = nx.Graph()
GRAPHS_DIR = "graphs"

# Ensure graphs directory exists
os.makedirs(GRAPHS_DIR, exist_ok=True)

def save_graph_to_file(name):
    graph_data = {
        'nodes': [
            {
                'id': node,
                'label': graph.nodes[node].get('label', node),
                'details': graph.nodes[node].get('details', {
                    'source_urls': [],
                    'author': '',
                    'date': '',
                    'description': ''
                })
            } 
            for node in graph.nodes()
        ],
        'edges': [{'source': u, 'target': v} for u, v in graph.edges()]
    }
    
    filename = os.path.join(GRAPHS_DIR, f"{name}.json")
    with open(filename, 'w') as f:
        json.dump(graph_data, f, indent=2)

def load_graph_from_file(name):
    global graph
    filename = os.path.join(GRAPHS_DIR, f"{name}.json")
    
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            
        graph = nx.Graph()
        for node in data['nodes']:
            graph.add_node(
                node['id'],
                label=node.get('label', node['id']),
                details=node.get('details', {
                    'source_urls': [],
                    'author': '',
                    'date': '',
                    'description': ''
                })
            )
        for edge in data['edges']:
            graph.add_edge(edge['source'], edge['target'])
        return True
    return False

def get_latest_autosave():
    files = [f for f in os.listdir(GRAPHS_DIR) if f.startswith('autosave_') and f.endswith('.json')]
    if not files:
        return None
    return os.path.splitext(max(files))[0]  # Return filename without extension

# Initialize with the latest autosave if available
latest_autosave = get_latest_autosave()
if latest_autosave:
    load_graph_from_file(latest_autosave)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    nodes = [
        {
            'id': node, 
            'label': graph.nodes[node].get('label', node),
            'details': graph.nodes[node].get('details', {
                'source_urls': [],
                'author': '',
                'date': '',
                'description': ''
            })
        } 
        for node in graph.nodes()
    ]
    edges = [{'source': u, 'target': v} for u, v in graph.edges()]
    return jsonify({'nodes': nodes, 'edges': edges})

@app.route('/api/node', methods=['POST'])
def add_node():
    data = request.json
    attributes = data.get('attributes', {})
    attributes['details'] = attributes.get('details', {
        'source_urls': [],
        'author': '',
        'date': '',
        'description': ''
    })
    graph.add_node(data['id'], **attributes)
    return jsonify({'status': 'success'})

@app.route('/api/node/<node_id>', methods=['DELETE'])
def delete_node(node_id):
    if node_id in graph:
        graph.remove_node(node_id)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Node not found'}), 404

@app.route('/api/edge', methods=['POST'])
def add_edge():
    data = request.json
    graph.add_edge(data['source'], data['target'])
    return jsonify({'status': 'success'})

@app.route('/api/node/details', methods=['POST'])
def update_node_details():
    data = request.json
    node_id = data.get('node_id')
    details = data.get('details', {})
    
    if node_id in graph:
        graph.nodes[node_id]['details'] = details
        # Auto-save the graph with a timestamp
        save_graph_to_file(f"autosave_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Node not found'}), 404

@app.route('/api/save', methods=['POST'])
def save_graph():
    data = request.json
    name = data.get('name', f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    save_graph_to_file(name)
    return jsonify({'status': 'success', 'name': name})

@app.route('/api/load/<name>', methods=['POST'])
def load_graph(name):
    if load_graph_from_file(name):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Graph not found'}), 404

@app.route('/api/graphs', methods=['GET'])
def list_graphs():
    graphs = [os.path.splitext(f)[0] for f in os.listdir(GRAPHS_DIR) 
             if f.endswith('.json')]
    return jsonify({'graphs': graphs})

if __name__ == '__main__':
    app.run(debug=True)
