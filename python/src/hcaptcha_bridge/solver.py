_E='Multiple hCaptcha widgets: pass widget_id to select one';_D='tiles';_C=False;_B=True;_A=None;import asyncio,time;from uuid import uuid4;from.api import API_ORIGIN,ApiClient;from.capture import TOKEN,capture,frame_info,same_pixels;from.errors import BridgeError,ChallengeChanged,NotReady;from.geometry import center,same_layout,to_viewport,validate_action
class HCaptchaSolver:
	def __init__(self,page,api_key,*,max_rounds=6,timeout=90,widget_id=_A,api_url=API_ORIGIN):
		if type(max_rounds)is not int or not 1<=max_rounds<=20 or not 0<timeout<=300:raise ValueError('Use max_rounds=1..20 and timeout=1..300 seconds')
		self.page,self.key,self.max_rounds,self.timeout=page,api_key,max_rounds,timeout;self.widget_id,self.api_url=widget_id,api_url;self._active_widget_id=widget_id;self.stats={};self._running=_C
	async def _token(self):
		for frame in self.page.frames:
			if frame_info(frame):continue
			try:
				A=await frame.evaluate(TOKEN,self._active_widget_id)
				if A:return A
			except Exception:
				if self.page.is_closed():raise BridgeError('The caller closed the page')from _A
	def _frames(self,kind):A=[(A,frame_info(A))for A in self.page.frames];return[B for(B,A)in A if A and A[0]==kind and(not self._active_widget_id or A[1]==self._active_widget_id)]
	def _bind_widget(self):
		if self._active_widget_id:return _B
		A={B[1]for A in self.page.frames if(B:=frame_info(A))and B[1]}
		if len(A)>1:raise BridgeError(_E)
		if A:self._active_widget_id=A.pop()
		return bool(self._active_widget_id)
	async def _visible(self,kind):
		A=[]
		for frame in self._frames(kind):
			B=_A
			try:
				B=await frame.frame_element()
				if await B.is_visible():A.append(frame)
			except Exception:continue
			finally:
				if B:await B.dispose()
		if len(A)>1:raise BridgeError(_E)
		return A[0]if A else _A
	async def _stable(self,frame):
		A=_A
		for C in range(8):
			try:
				B=await capture(frame)
				if A and same_layout(A,B)and same_pixels(A,B):return B
				A=B
			except NotReady:A=_A
			await asyncio.sleep(.25)
	async def _apply(self,plan,snapshot):
		O='submit';N='grid';M='target';L='source';J='type';E='box';C,F=[],[];G=0;frame=snapshot['frame']
		async def P():
			B='Challenge changed before the remaining actions'
			try:A=await capture(frame)
			except NotReady:
				if not G:raise
				raise ChallengeChanged(B)from _A
			if not same_layout(snapshot,A)or not same_pixels(snapshot,A,C,F):
				if not G:raise NotReady('Challenge changed before the first action')
				raise ChallengeChanged(B)
			return A
		for A in plan.get('indices',plan.get('points',plan.get('moves',[]))):
			D=await P();G+=1
			if plan[J]=='drag':
				H,I=to_viewport(A[L],D[E]);Q,R=to_viewport(A[M],D[E]);await self.page.mouse.move(H,I);await self.page.mouse.down()
				try:
					for K in range(1,25):await self.page.mouse.move(H+(Q-H)*K/24,I+(R-I)*K/24);await asyncio.sleep(.016)
				finally:await self.page.mouse.up()
				C.extend((A[L],A[M]))
			else:
				S=center(D[_D][A])if plan[J]==N else A;await self.page.mouse.click(*to_viewport(S,D[E]),delay=60)
				if plan[J]==N:F.append(snapshot[_D][A])
				else:C.append(A)
			await asyncio.sleep(.12)
		try:B=await capture(frame)
		except NotReady:return snapshot
		if not same_layout(snapshot,B):return snapshot
		if not same_pixels(snapshot,B,C,F):raise ChallengeChanged('Challenge changed before submission')
		if not B[O]or B['disabled']:raise BridgeError('The challenge submit button is unavailable')
		await self.page.mouse.click(*to_viewport(center(B[O]),B[E]),delay=60);return B
	async def solve(self):
		U='token_issued';T='operations';S='charged_micro_usd';R='visual';L='discarded';K='rounds';C='reason'
		if self._running:raise BridgeError('This solver is already running')
		E=ApiClient(self.key,self.api_url);self._running=_B;self._active_widget_id=self.widget_id;M=time.monotonic();I=M+self.timeout;self.stats={K:0,R:_C,S:0,T:[],L:0,C:_A};B=_A;J=_A;A=_A;N=_C
		try:
			async with asyncio.timeout(self.timeout):
				while _B:
					F=await self._token()if self._bind_widget()else _A
					if F:
						if A:await E.feedback(A,_B,I)
						self.stats[C]=U;return F
					frame=await self._visible('challenge')
					if not frame:
						if not N:
							O=await self._visible('checkbox')
							if O:V=O.locator('#checkbox,[role="checkbox"]').first;await V.click(timeout=2000);N=_B
						await asyncio.sleep(.3);continue
					try:snapshot=await self._stable(frame)
					except NotReady:continue
					if not snapshot:continue
					self.stats[R]=_B
					if snapshot['rejected']:
						if A:await E.feedback(A,_C,I);A=_A
						if not B or any(A and same_layout(A,snapshot)and same_pixels(A,snapshot)for A in(B,J)):await asyncio.sleep(.3);continue
					if B:
						if same_layout(B,snapshot)and same_pixels(B,snapshot):await asyncio.sleep(.3);continue
						B,J,A=_A,_A,_A
					if self.stats[K]>=self.max_rounds:self.stats[C]='max_rounds';return
					P,W=str(uuid4()),str(uuid4());Q={A:snapshot[A]for A in('question','image','canvases',_D)};Q.update(protocol='1',challenge_id=P,references=snapshot['referenceImages']);self.stats[K]+=1;D=await E.solve(Q,W,I);self.stats[T].append(D.get('id'));self.stats[S]+=D.get('billing',{}).get('charged',0);G=D.get('result')
					if D.get('status')!='ready'or D.get('result_expired')or not isinstance(G,dict):raise BridgeError('API request failed or its result expired')
					if G.get('protocol')!='1'or G.get('challenge_id')!=P or G.get('coordinate_space')!='full_challenge_image_0_1000':raise BridgeError('Discarded an incompatible or mismatched result')
					plan=validate_action(G.get('action'),snapshot);H=await self._stable(frame)
					if not H or not same_layout(snapshot,H)or not same_pixels(snapshot,H):self.stats[L]+=1;continue
					A=D['id']
					try:B=await self._apply(plan,H);J=H
					except NotReady:self.stats[L]+=1;A=_A;continue
					except ChallengeChanged:
						F=await self._token()
						if F:await E.feedback(A,_B,I);self.stats[C]=U;return F
						raise
					await asyncio.sleep(.35)
		except TimeoutError:self.stats[C]='timeout';return
		except asyncio.CancelledError:self.stats[C]='cancelled';raise
		except Exception:self.stats[C]='error';raise
		finally:
			try:await self.page.mouse.up()
			except Exception:0
			await E.close();self.stats['elapsed_seconds']=round(time.monotonic()-M,3);self._running=_C
