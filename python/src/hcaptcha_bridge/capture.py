_N='moving';_M='question';_L='maximum';_K='minimum';_J=False;_I='references';_H='tiles';_G='animation';_F='sample';_E='canvases';_D='height';_C='width';_B='y';_A='x';import base64,io,math,re;from importlib.resources import files;from urllib.parse import parse_qs,urlsplit;from PIL import Image;from.errors import BridgeError,NotReady;from.geometry import same_layout;METADATA=files('hcaptcha_bridge').joinpath('widget.js').read_text();FRAME_STYLE="el => {\n  for (let n=el; n; n=n.parentElement) {\n    const s=getComputedStyle(n);\n    if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0) return null;\n    if(s.transform!=='none') {const m=new DOMMatrix(s.transform);\n      if(!m.is2D||Math.abs(m.b)>.001||Math.abs(m.c)>.001||m.a<=0||m.d<=0) throw Error('Unsupported iframe transform');}\n  }\n  const s=getComputedStyle(el), r=el.getBoundingClientRect();\n  return {left:parseFloat(s.borderLeftWidth)||0,top:parseFloat(s.borderTopWidth)||0,\n    right:parseFloat(s.borderRightWidth)||0,bottom:parseFloat(s.borderBottomWidth)||0,\n    sx:r.width/el.offsetWidth,sy:r.height/el.offsetHeight};\n}";TOKEN='id => {\n const fields=[...document.querySelectorAll(\'[name="h-captcha-response"],[name="g-recaptcha-response"]\')];\n const selected=id?fields.filter(e=>e.id===`h-captcha-response-${id}`||e.id===`g-recaptcha-response-${id}`):fields;\n return selected.map(e=>e.value?.trim()).find(Boolean)||null;\n}'
def frame_info(frame):
	try:
		A=urlsplit(frame.url)
		if A.hostname!='hcaptcha.com'and not(A.hostname or'').endswith('.hcaptcha.com'):return
		B=parse_qs(A.fragment);C=B.get('frame',[''])[0];return(C,B.get('id',[''])[0])if C in('checkbox','challenge')else None
	except ValueError:return
def encode(image):A=io.BytesIO();image.save(A,format='PNG');return base64.b64encode(A.getvalue()).decode()
def images(raw,inset,meta):
	with Image.open(io.BytesIO(raw))as B:
		if B.width*B.height>8000000:raise BridgeError('Challenge capture exceeds 8 megapixels')
		image=B.convert('RGB')
	F,G,H,I=inset;image=image.crop((round(F),round(G),image.width-round(H),image.height-round(I)));C=[]
	for A in meta[_I]:
		J=A[_A]*image.width/1000,A[_B]*image.height/1000,(A[_A]+A[_C])*image.width/1000,(A[_B]+A[_D])*image.height/1000;D=image.crop(tuple(round(A)for A in J))
		if min(D.size)<8:raise BridgeError('Reference image is smaller than 8 pixels')
		C.append(encode(D))
	K=image.resize((100,100),Image.Resampling.NEAREST);E=K.tobytes();return encode(image),C,[tuple(E[A:A+3])for A in range(0,len(E),3)]
def valid_meta(meta):
	if not meta[_M]or meta['loading']or not meta[_E]and len(meta[_H])!=9:raise NotReady('Waiting for a visual challenge')
	if len(meta[_E])>8 or len(meta[_I])>9 or len(meta[_H])not in(0,9):raise BridgeError('Unsupported challenge layout')
	for A in[*meta[_E],*meta[_H],*meta[_I]]:
		if any(not math.isfinite(A[B])for B in(_A,_B,_C,_D))or min(A[_A],A[_B])<0 or min(A[_C],A[_D])<=0 or A[_A]+A[_C]>1000.01 or A[_B]+A[_D]>1000.01:raise BridgeError('Interaction area lies outside the challenge')
async def capture(frame):
	F='Challenge is hidden';E='box';C=await frame.frame_element()
	try:
		if not await C.is_visible():raise NotReady(F)
		await C.scroll_into_view_if_needed(timeout=1500);A=await C.evaluate(FRAME_STYLE);B=await C.bounding_box()
		if not A or not B or min(B[_C],B[_D])<30:raise NotReady(F)
		inset=[A['left']*A['sx'],A['top']*A['sy'],A['right']*A['sx'],A['bottom']*A['sy']];D={_A:B[_A]+inset[0],_B:B[_B]+inset[1],_C:B[_C]-inset[0]-inset[2],_D:B[_D]-inset[1]-inset[3]}
		if D[_C]>2200 or D[_D]>2200:raise BridgeError('Challenge iframe is too large')
		meta=await frame.evaluate(METADATA);valid_meta(meta);raw=await C.screenshot(type='png',scale='css',timeout=2000);after=await frame.evaluate(METADATA)
		if not same_layout({**meta,E:D},{**after,E:D}):raise NotReady('Challenge changed during capture')
		image,G,H=images(raw,inset,meta);return{**meta,E:D,'image':image,'referenceImages':G,_F:H,'frame':frame}
	finally:await C.dispose()
def same_pixels(a,b,masks=(),cells=()):
	O='prompt';P=[*a[_E],*a[_H],*a[_I],*([a[O]]if a[O]else[])];Q=len(a[_E])+len(a[_H]);L=_J
	for(M,A)in enumerate(P):
		F=G=B=H=0;C=a.get(_G,{}).get(_N)if M<len(a[_E])else None
		for D in range(100):
			for E in range(100):
				I,J=E*10,D*10
				if not(A[_A]<I<A[_A]+A[_C]and A[_B]<J<A[_B]+A[_D]):continue
				if M<Q and(any(abs(I-A[0])<100 and abs(J-A[1])<100 for A in masks)or any(A[_A]-10<=I<=A[_A]+A[_C]+10 and A[_B]-10<=J<=A[_B]+A[_D]+10 for A in cells)):continue
				if C and C[D*100+E]:continue
				for(N,(before,after))in enumerate(zip(a[_F][D*100+E],b[_F][D*100+E])):K=max(0,a[_G][_K][D*100+E][N]-after,after-a[_G][_L][D*100+E][N])if C else abs(before-after);F+=K;G+=K>(25 if C else 20);H=max(H,K);B+=1
		if B:
			L=True
			if C and(F/B>.25 or G/B>.001 or H>64)or not C and(F/B>=3 or G/B>=.035):return _J
	return L
def temporal_snapshot(samples):
	if len(samples)<8:return
	A=samples[-1]
	if not re.search('\\b(select|click|find|selecione|clique|encontre)\\b',A[_M],re.I):return
	if len(A[_E])!=1 or A[_H]or any(not same_layout(A,B)for B in samples):return
	B=A[_E][0];C=[B[_A]<A%100*10<B[_A]+B[_C]and B[_B]<A//100*10<B[_B]+B[_D]for A in range(10000)];G=[C[A]and any(max(C[_F][A][B]for C in samples[:-2])-min(C[_F][A][B]for C in samples[:-2])>12 for B in range(3))for A in range(10000)];D=[C[A]and any(G[B*100+C]for B in range(max(0,A//100-1),min(100,A//100+2))for C in range(max(0,A%100-1),min(100,A%100+2)))for A in range(10000)];E=sum(D)/max(1,sum(C))
	if not .001<=E<=.25:return
	H=[[min(C[_F][A][B]for C in samples[:-2])for B in range(3)]for A in range(10000)];I=[[max(C[_F][A][B]for C in samples[:-2])for B in range(3)]for A in range(10000)];F={**samples[-3],_G:{_N:D,'fraction':E,_K:H,_L:I}}
	if not all(same_pixels(F,A)for A in samples[-2:]):return
	J=sorted({round(A*(len(samples)-2)/4)for A in range(5)});return{**A,_G:F[_G],'temporal_frames':[samples[A]['image']for A in J]}
def selected_animation(before,after,masks,cells):
	if not before.get(_G):return after
	A={**before[_G]}
	for C in(_K,_L):
		A[C]=list(A[C])
		for B in range(10000):
			D,E=B%100*10,B//100*10
			if any(abs(D-A[0])<100 and abs(E-A[1])<100 for A in masks)or any(A[_A]-10<=D<=A[_A]+A[_C]+10 and A[_B]-10<=E<=A[_B]+A[_D]+10 for A in cells):A[C][B]=after[_F][B]
	return{**after,_G:A}
def static_samples(samples):
	if len(samples)<4:return _J
	B=samples[-4:]
	if not B[-1][_E]:return True
	for A in B[-1][_E]:
		C=[B for B in range(10000)if A[_A]<B%100*10<A[_A]+A[_C]and A[_B]<B//100*10<A[_B]+A[_D]];D=sum(any(max(B[_F][A][C]for B in B)-min(B[_F][A][C]for B in B)>12 for C in range(3))for A in C)
		if D/max(1,len(C))>.001:return _J
	return True
