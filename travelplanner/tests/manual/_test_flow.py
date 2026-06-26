import sys
import time

print("=== Test 1: RAG Agent ===")
try:
    from agents.rag_agent import RAGAgent
    t0 = time.time()
    r = RAGAgent().run({"destination_city": "Barcelona"})
    print(f"  OK ({time.time()-t0:.1f}s): rag_data keys={list(r.get('rag_data',{}).keys())}")
except Exception as e:
    print(f"  FAIL: {e}")

print("\n=== Test 2: Planner Agent ===")
try:
    from agents.planner_agent import PlannerAgent
    t0 = time.time()
    p = PlannerAgent().plan_trip("Barcelona", 3, context="Ciudad costera con playas y cultura.")
    print(f"  OK ({time.time()-t0:.1f}s): summary={len(p['summary'])} chars")
except Exception as e:
    print(f"  FAIL: {e}")

print("\n=== Test 3: Itinerary Agent ===")
try:
    from agents.itinerary_agent import ItineraryAgent
    t0 = time.time()
    i = ItineraryAgent().build_itinerary("Barcelona", 3, planner_summary="Plan de 3 dias en Barcelona", attractions=[], rag_data={})
    print(f"  OK ({time.time()-t0:.1f}s): days={len(i['itinerary'])}")
    for d in i['itinerary']:
        print(f"    - {d['title']}: {d['description'][:60]}... acts={d['suggested_activities']}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"  FAIL: {e}")

print("\n=== Test 4: Full ejecutar_viaje ===")
try:
    from graph.graph import ejecutar_viaje
    t0 = time.time()
    r = ejecutar_viaje("Barcelona", 3)
    print(f"  OK ({time.time()-t0:.1f}s)")
    print(f"  motivacional: {r['mensaje_motivacional'][:100] if r['mensaje_motivacional'] else 'NONE'}")
    print(f"  atracciones: {len(r['opciones_busqueda'])} items")
    it = r['itinerario']
    for d in it.get('days', []):
        print(f"    - {d.get('title','')}: {d.get('description','')[:60]}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"  FAIL: {e}")
