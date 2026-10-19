_H='sample';_G='references';_F='tiles';_E='canvases';_D='height';_C='width';_B='y';_A='x';import base64,io,math;from importlib.resources import files;from urllib.parse import parse_qs,urlsplit;from PIL import Image;from.errors import BridgeError,NotReady;from.geometry import same_layout;METADATA=files('hcaptcha_bridge').joinpath('widget.js').read_text();FRAME_STYLE="el => {\n  for (let n=el; n; n=n.parentElement) {\n    const s=getComputedStyle(n);\n    if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0) return null;\n    if(s.transform!=='none') {const m=new DOMMatrix(s.transform);\n      if(!m.is2D||Math.abs(m.b)>.001||Math.abs(m.c)>.001||m.a<=0||m.d<=0) throw Error('Unsupported iframe transform');}\n  }\n  const s=getComputedStyle(el), r=el.getBoundingClientRect();\n  return {left:parseFloat(s.borderLeftWidth)||0,top:parseFloat(s.borderTopWidth)||0,\n    right:parseFloat(s.borderRightWidth)||0,bottom:parseFloat(s.borderBottomWidth)||0,\n    sx:r.width/el.offsetWidth,sy:r.height/el.offsetHeight};\n}";TOKEN='id => {\n const fields=[...document.querySelectorAll(\'[name="h-captcha-response"],[name="g-recaptcha-response"]\')];\n const selected=id?fields.filter(e=>e.id===`h-captcha-response-${id}`||e.id===`g-recaptcha-response-${id}`):fields;\n return selected.map(e=>e.value?.trim()).find(Boolean)||null;\n}'
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
	for A in meta[_G]:
		J=A[_A]*image.width/1000,A[_B]*image.height/1000,(A[_A]+A[_C])*image.width/1000,(A[_B]+A[_D])*image.height/1000;D=image.crop(tuple(round(A)for A in J))
		if min(D.size)<8:raise BridgeError('Reference image is smaller than 8 pixels')
		C.append(encode(D))
	K=image.resize((100,100),Image.Resampling.NEAREST);E=K.tobytes();return encode(image),C,[tuple(E[A:A+3])for A in range(0,len(E),3)]
def valid_meta(meta):
	if not meta['question']or meta['loading']or not meta[_E]and len(meta[_F])!=9:raise NotReady('Waiting for a visual challenge')
	if len(meta[_E])>8 or len(meta[_G])>9 or len(meta[_F])not in(0,9):raise BridgeError('Unsupported challenge layout')
	for A in[*meta[_E],*meta[_F],*meta[_G]]:
		if any(not math.isfinite(A[B])for B in(_A,_B,_C,_D))or min(A[_A],A[_B])<0 or min(A[_C],A[_D])<=0 or A[_A]+A[_C]>1000.01 or A[_B]+A[_D]>1000.01:raise BridgeError('Interaction area lies outside the challenge')
async def capture(frame):
	F='Challenge is hidden';E='box';C=await frame.frame_element()
	try:
		if not await C.is_visible():raise NotReady(F)
		await C.scroll_into_view_if_needed(timeout=1500);A=await C.evaluate(FRAME_STYLE);B=await C.bounding_box()
		if not A or not B or min(B[_C],B[_D])<30:raise NotReady(F)
		inset=[A['left']*A['sx'],A['top']*A['sy'],A['right']*A['sx'],A['bottom']*A['sy']];D={_A:B[_A]+inset[0],_B:B[_B]+inset[1],_C:B[_C]-inset[0]-inset[2],_D:B[_D]-inset[1]-inset[3]}
		if D[_C]>2200 or D[_D]>2200:raise BridgeError('Challenge iframe is too large')
		meta=await frame.evaluate(METADATA);valid_meta(meta);raw=await C.screenshot(type='png',scale='css',timeout=2000);G=await frame.evaluate(METADATA)
		if not same_layout({**meta,E:D},{**G,E:D}):raise NotReady('Challenge changed during capture')
		image,H,I=images(raw,inset,meta);return{**meta,E:D,'image':image,'referenceImages':H,_H:I,'frame':frame}
	finally:await C.dispose()
def same_pixels(a,b,masks=(),cells=()):
	L=False;K='prompt';M=[*a[_E],*a[_F],*a[_G],*([a[K]]if a[K]else[])];N=len(a[_E])+len(a[_F]);G=L
	for(O,A)in enumerate(M):
		H=I=B=0
		for C in range(100):
			for D in range(100):
				E,F=D*10,C*10
				if not(A[_A]<E<A[_A]+A[_C]and A[_B]<F<A[_B]+A[_D]):continue
				if O<N and(any(abs(E-A[0])<100 and abs(F-A[1])<100 for A in masks)or any(A[_A]-10<=E<=A[_A]+A[_C]+10 and A[_B]-10<=F<=A[_B]+A[_D]+10 for A in cells)):continue
				for(P,Q)in zip(a[_H][C*100+D],b[_H][C*100+D]):J=abs(P-Q);H+=J;I+=J>20;B+=1
		if B:
			G=True
			if H/B>=3 or I/B>=.035:return L
	return G
