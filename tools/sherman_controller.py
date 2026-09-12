"""Controller travel for in-place Sherman previews, in world scene units."""
def controller_distance(spec, frame):
    keys=spec.get('controller_travel_keys',[])
    if not keys:return 0.0
    x=[k['frame'] for k in keys];y=[k['distance'] for k in keys]
    slopes=[(y[i+1]-y[i])/(x[i+1]-x[i]) for i in range(len(x)-1)]
    tangents=[0.0]
    for a,b in zip(slopes,slopes[1:]):tangents.append(2*a*b/(a+b) if a*b>0 else 0.0)
    tangents.append(0.0)
    if frame<=x[0]:return y[0]
    for i in range(len(x)-1):
        if frame<=x[i+1]:
            h=x[i+1]-x[i];t=(frame-x[i])/h
            return (2*t**3-3*t*t+1)*y[i]+(t**3-2*t*t+t)*h*tangents[i]+(-2*t**3+3*t*t)*y[i+1]+(t**3-t*t)*h*tangents[i+1]
    return y[-1]
