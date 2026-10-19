_C='canvases';_B='height';_A='width';import math;from.errors import BridgeError
def point(value):return isinstance(value,list)and len(value)==2 and all(type(A)is int and 0<A<1000 for A in value)
def validate_action(action,snapshot):
	P='moves';O='drag';N='points';M='point';L='indices';K='grid';J='type';H='target';F='source'
	def G(p):return any(A['x']<p[0]<A['x']+A[_A]and A['y']<p[1]<A['y']+A[_B]for A in snapshot[_C])
	if not isinstance(action,dict):raise BridgeError('API result has no action')
	A=action.get(J)
	if A==K:B=action.get(L);E=len(snapshot['tiles'])==9 and isinstance(B,list)and 1<=len(B)<=9 and all(type(A)is int and 0<=A<=8 for A in B)and len(set(B))==len(B)
	elif A==M:C=action.get(N);E=isinstance(C,list)and 1<=len(C)<=9 and all(point(p)and G(p)for p in C)and len({tuple(p)for p in C})==len(C)
	elif A==O:D=action.get(P);E=isinstance(D,list)and 1<=len(D)<=6 and all(isinstance(A,dict)and point(A.get(F))and point(A.get(H))and G(A[F])and G(A[H])and A[F]!=A[H]for A in D)and len({tuple(A[F])for A in D})==len(D)
	else:E=False
	if not E:raise BridgeError('Invalid or unsupported action; no clicks were applied')
	I={K:L,M:N,O:P}[A];return{J:A,I:action[I]}
def same_layout(a,b):A='box';B='question',_C,'tiles','tileSources','references','referenceSources','prompt';return all(a.get(A)==b.get(A)for A in B)and all(abs(a[A][B]-b[A][B])<1 for B in(_A,_B))
def to_viewport(p,box):
	if not point(p)or any(not math.isfinite(box[A])for A in('x','y',_A,_B)):raise BridgeError('Invalid browser coordinate')
	return box['x']+p[0]*box[_A]/1000,box['y']+p[1]*box[_B]/1000
def center(rect):return[round(rect['x']+rect[_A]/2),round(rect['y']+rect[_B]/2)]
