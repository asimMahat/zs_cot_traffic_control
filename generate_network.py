
"""
Optional: Programmatically generate nodes.nod.xml and edges.edg.xml for a symmetric 4-leg intersection.
"""
import xml.etree.ElementTree as ET

nodes = ET.Element('nodes')
for node_id, x, y, ntype in [
    ('N', 0, 50, 'priority'),
    ('E', 50, 0, 'priority'),
    ('S', 0, -50, 'priority'),
    ('W', -50, 0, 'priority'),
    ('C', 0, 0, 'traffic_light'),
]:
    ET.SubElement(nodes, 'node', id=node_id, x=str(x), y=str(y), type=ntype)

edges = ET.Element('edges')
edge_defs = [
    ('N2C', 'N', 'C'), ('C2S', 'C', 'S'),
    ('S2C', 'S', 'C'), ('C2N', 'C', 'N'),
    ('E2C', 'E', 'C'), ('C2W', 'C', 'W'),
    ('W2C', 'W', 'C'), ('C2E', 'C', 'E'),
]
# for eid, frm, to in edge_defs:
#     ET.SubElement(edges, 'edge', id=eid, from=frm, to=to, priority='1', numLanes='1', speed='13.9')

for eid, frm, to in edge_defs:
    edge_attrs = {
        'id': eid,
        'from': frm,
        'to': to,
        'priority': '1',
        'numLanes': '1',
        'speed': '13.9'
    }
    ET.SubElement(edges, 'edge', **edge_attrs)

ET.ElementTree(nodes).write('nodes.nod.xml', encoding='utf-8', xml_declaration=True)
ET.ElementTree(edges).write('edges.edg.xml', encoding='utf-8', xml_declaration=True)
