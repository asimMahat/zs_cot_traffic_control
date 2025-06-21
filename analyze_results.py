#!/usr/bin/env python3
"""
SUMO Simulation Results Analyzer
Analyzes output files from SUMO simulations to provide insights without GUI
"""

import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

def analyze_tripinfo():
    """Analyze trip information from tripinfo.xml"""
    if not os.path.exists('tripinfo.xml'):
        print("tripinfo.xml not found. Run simulation first.")
        return
    
    print("=== TRIP ANALYSIS ===")
    tree = ET.parse('tripinfo.xml')
    root = tree.getroot()
    
    trips = []
    for trip in root.findall('tripinfo'):
        trip_data = {
            'id': trip.get('id'),
            'depart': float(trip.get('depart', 0)),
            'arrival': float(trip.get('arrival', 0)),
            'duration': float(trip.get('duration', 0)),
            'waitingTime': float(trip.get('waitingTime', 0)),
            'timeLoss': float(trip.get('timeLoss', 0)),
            'routeLength': float(trip.get('routeLength', 0))
        }
        trips.append(trip_data)
    
    if trips:
        df = pd.DataFrame(trips)
        print(f"Total trips: {len(trips)}")
        print(f"Average trip duration: {df['duration'].mean():.2f} seconds")
        print(f"Average waiting time: {df['waitingTime'].mean():.2f} seconds")
        print(f"Average time loss: {df['timeLoss'].mean():.2f} seconds")
        print(f"Total route length: {df['routeLength'].sum():.2f} meters")
        
        # Create histogram of trip durations
        plt.figure(figsize=(10, 6))
        plt.hist(df['duration'], bins=20, alpha=0.7, color='blue')
        plt.xlabel('Trip Duration (seconds)')
        plt.ylabel('Number of Vehicles')
        plt.title('Distribution of Trip Durations')
        plt.savefig('trip_durations.png')
        plt.close()
        print("Saved trip_durations.png")
        
        return df
    else:
        print("No trip data found")
        return None

def analyze_summary():
    """Analyze simulation summary from summary.xml"""
    if not os.path.exists('summary.xml'):
        print("summary.xml not found. Run simulation first.")
        return
    
    print("\n=== SIMULATION SUMMARY ===")
    tree = ET.parse('summary.xml')
    root = tree.getroot()
    
    # Extract key statistics
    for stat in root.findall('statistics'):
        print(f"Simulation time: {stat.get('time', 'N/A')} seconds")
        print(f"Number of vehicles: {stat.get('vehicles', 'N/A')}")
        print(f"Number of trips: {stat.get('trips', 'N/A')}")
        print(f"Average speed: {stat.get('avgSpeed', 'N/A')} m/s")
        print(f"Average waiting time: {stat.get('avgWaitingTime', 'N/A')} seconds")

def analyze_queue_data():
    """Analyze queue data from queue.xml"""
    if not os.path.exists('queue.xml'):
        print("queue.xml not found. Run simulation first.")
        return
    
    print("\n=== QUEUE ANALYSIS ===")
    tree = ET.parse('queue.xml')
    root = tree.getroot()
    
    queues = []
    for queue in root.findall('queue'):
        queue_data = {
            'edge': queue.get('edge'),
            'time': float(queue.get('time', 0)),
            'length': float(queue.get('length', 0)),
            'vehicles': queue.get('vehicles', '')
        }
        queues.append(queue_data)
    
    if queues:
        df = pd.DataFrame(queues)
        print(f"Queue measurements: {len(queues)}")
        print(f"Maximum queue length: {df['length'].max():.2f} meters")
        print(f"Average queue length: {df['length'].mean():.2f} meters")
        
        # Create queue length over time plot
        plt.figure(figsize=(12, 6))
        for edge in df['edge'].unique():
            edge_data = df[df['edge'] == edge]
            plt.plot(edge_data['time'], edge_data['length'], label=edge, marker='o', markersize=2)
        
        plt.xlabel('Time (seconds)')
        plt.ylabel('Queue Length (meters)')
        plt.title('Queue Lengths Over Time by Edge')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('queue_analysis.png')
        plt.close()
        print("Saved queue_analysis.png")
        
        return df
    else:
        print("No queue data found")
        return None

def analyze_edge_data():
    """Analyze edge data from edge_data.xml"""
    if not os.path.exists('edge_data.xml'):
        print("edge_data.xml not found. Run simulation first.")
        return
    
    print("\n=== EDGE ANALYSIS ===")
    tree = ET.parse('edge_data.xml')
    root = tree.getroot()
    
    edges = []
    for interval in root.findall('interval'):
        for edge in interval.findall('edge'):
            edge_data = {
                'id': edge.get('id'),
                'time': float(interval.get('begin', 0)),
                'density': float(edge.get('density', 0)),
                'flow': float(edge.get('flow', 0)),
                'speed': float(edge.get('speed', 0)),
                'waitingTime': float(edge.get('waitingTime', 0))
            }
            edges.append(edge_data)
    
    if edges:
        df = pd.DataFrame(edges)
        print(f"Edge measurements: {len(edges)}")
        print(f"Average density: {df['density'].mean():.2f} vehicles/km")
        print(f"Average flow: {df['flow'].mean():.2f} vehicles/hour")
        print(f"Average speed: {df['speed'].mean():.2f} m/s")
        
        # Create edge performance heatmap
        pivot_df = df.pivot_table(values='density', index='time', columns='id', aggfunc='mean')
        plt.figure(figsize=(12, 8))
        plt.imshow(pivot_df.T, aspect='auto', cmap='YlOrRd')
        plt.colorbar(label='Density (vehicles/km)')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Edge ID')
        plt.title('Traffic Density Heatmap')
        plt.savefig('edge_density_heatmap.png')
        plt.close()
        print("Saved edge_density_heatmap.png")
        
        return df
    else:
        print("No edge data found")
        return None

def print_simulation_insights():
    """Print key insights from the simulation"""
    print("\n" + "="*50)
    print("SIMULATION INSIGHTS")
    print("="*50)
    
    # Check which files exist and analyze them
    files_to_analyze = [
        ('tripinfo.xml', analyze_tripinfo),
        ('summary.xml', analyze_summary),
        ('queue.xml', analyze_queue_data),
        # ('edge_data.xml', analyze_edge_data) # This output is disabled for now
    ]
    
    for filename, analyzer in files_to_analyze:
        if os.path.exists(filename):
            analyzer()
        else:
            print(f"\n{filename} not found - run simulation with output enabled")

def main():
    """Main analysis function"""
    print("SUMO Simulation Results Analyzer")
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print_simulation_insights()
    
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)
    print("Generated files:")
    print("- trip_durations.png (if trip data available)")
    print("- queue_analysis.png (if queue data available)")
    # print("- edge_density_heatmap.png (if edge data available)")

if __name__ == "__main__":
    main() 