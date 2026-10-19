_A=None;import asyncio,math,re,time;from datetime import datetime,timezone;from email.utils import parsedate_to_datetime;from urllib.parse import urlsplit;import httpx;from.errors import ApiError,BridgeError;API_ORIGIN='https://api.hcaptchasolver.org'
def retry_delay(value):
	A=1.
	try:B=float(value);return max(A,B)if math.isfinite(B)else A
	except(ValueError,TypeError):
		try:return max(A,(parsedate_to_datetime(value)-datetime.now(timezone.utc)).total_seconds())
		except(ValueError,TypeError,OverflowError):return A
def origin(value):
	A=urlsplit(value)
	if not A.hostname or A.username or A.password or A.path not in('','/')or A.query or A.fragment or not(A.scheme=='https'or A.scheme=='http'and A.hostname in('localhost','127.0.0.1')):raise ValueError('API URL must be an HTTPS origin (loopback HTTP is allowed for tests)')
	B=A.port;return value.rstrip('/')
def task_path(value):
	if not isinstance(value,str)or not re.fullmatch('[A-Za-z0-9_-]{1,100}',value):raise BridgeError('Invalid operation ID')
	return'/tasks/'+value
class ApiClient:
	def __init__(self,key,api_url=API_ORIGIN,*,transport=_A):
		if not key or not key.strip():raise ValueError('Set HCAPTCHA_API_KEY to a customer API key')
		self.client=httpx.AsyncClient(base_url=origin(api_url)+'/v2',follow_redirects=False,headers={'Authorization':'Bearer '+key,'Accept-Language':'en'},transport=transport)
	async def close(self):await self.client.aclose()
	async def request(self,method,path,deadline,*,body=_A,idem=_A):
		F='http_error'
		for D in range(3):
			E=deadline-time.monotonic()
			if E<=0:raise TimeoutError
			try:A=await self.client.request(method,path,json=body,headers={'Idempotency-Key':idem}if idem else{},timeout=min(40,E))
			except httpx.TransportError:
				if D==2:raise ApiError(0,'network_uncertain',idempotency_key=idem)from _A
				C=1
			else:
				try:B=A.json()
				except ValueError:B={}
				if A.is_success:
					if not isinstance(B,dict):raise BridgeError('Invalid API response')
					return B
				G=B.get('error',F)if isinstance(B,dict)else F
				if A.status_code not in(429,502,503,504)or D==2:raise ApiError(A.status_code,str(G)[:100],idempotency_key=idem)
				C=retry_delay(A.headers.get('Retry-After'))
			if C>=deadline-time.monotonic():raise TimeoutError
			await asyncio.sleep(C)
		raise AssertionError('unreachable')
	async def solve(self,payload,idem,deadline):
		A=await self.request('POST','/solutions',deadline,body=payload,idem=idem)
		while A.get('status')in('queued','running'):await asyncio.sleep(min(2,max(0,deadline-time.monotonic())));A=await self.request('GET',task_path(A.get('id')),deadline)
		return A
	async def feedback(self,task_id,success,deadline):
		try:await self.request('POST',task_path(task_id)+'/feedback',min(deadline,time.monotonic()+3),body={'success':success})
		except(ApiError,TimeoutError):0
