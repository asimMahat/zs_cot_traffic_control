"""
Simple route generator for 4-leg intersection.
"""
from sumolib import net
import xml.etree.ElementTree as ET

# Define flows here
flows = [
    {'id': 'f_north_south', 'route': ['N2TL', 'TL2S'], 'begin': 0, 'end': 3600, 'rate': 600},
    {'id': 'f_west_east',   'route': ['W2TL', 'TL2E'], 'begin': 0, 'end': 3600, 'rate': 600},
    # add more as needed
]

root = ET.Element('routes')
ET.SubElement(root, 'vType', id='car', accel='2.6', decel='4.5', sigma='0.5', length='5', maxSpeed='13.9')
for f in flows:
    r = ET.SubElement(root, 'flow', id=f['id'], begin=str(f['begin']), end=str(f['end']), vehsPerHour=str(f['rate']))
    ET.SubElement(r, 'route', edges=' '.join(f['route']))

tree = ET.ElementTree(root)
tree.write('routes.rou.xml', encoding='utf-8', xml_declaration=True)