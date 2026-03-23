from django.shortcuts import render
from django.http import JsonResponse
from .simulation import AODVSimulation

def index(request):
    """Render the main visualization page."""
    return render(request, 'manet/simulation.html')

def run_simulation(request):
    """Run a simulation and return the sequence of events as JSON."""
    try:
        nodes = int(request.GET.get('nodes', 15))
        wifi_range = int(request.GET.get('range', 150))
        steps = int(request.GET.get('steps', 200))
        generate_traffic = request.GET.get('traffic', 'true').lower() == 'true'
        
        sim = AODVSimulation(num_nodes=nodes, wifi_range=wifi_range)
        history = sim.simulate_scenario(steps=steps)
        
        return JsonResponse({
            'status': 'success',
            'history': history,
            'config': {
                'nodes': nodes,
                'wifi_range': wifi_range,
                'steps': steps
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
