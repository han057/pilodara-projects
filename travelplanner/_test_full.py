import sys, io, time, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=== Starting ejecutar_viaje ===", flush=True)

t0 = time.time()
try:
    from graph.graph import ejecutar_viaje
    r = ejecutar_viaje('Barcelona', 3)
    elapsed = time.time() - t0

    print(f"\n=== RESULT ({elapsed:.0f}s) ===", flush=True)
    print(f"PLAN: {r.get('mensaje_motivacional', 'NONE')[:400]}")
    print(f"ATRACCIONES: {len(r.get('opciones_busqueda', []))} items")
    it = r.get('itinerario', {})
    print(f"ITINERARIO: {len(it.get('days', []))} days")
    for d in it.get('days', []):
        print(f"  - {d.get('title','')}: {d.get('description','')[:80]}")
        print(f"    acts: {d.get('suggested_activities', [])}")
except Exception:
    elapsed = time.time() - t0
    print(f"\nFAILED after {elapsed:.0f}s", flush=True)
    traceback.print_exc()

print("\nDONE", flush=True)
