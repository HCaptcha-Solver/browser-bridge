class BridgeError(Exception):0
class ChallengeChanged(BridgeError):0
class NotReady(BridgeError):0
class ApiError(BridgeError):
	def __init__(self,status,code,*,idempotency_key=None):super().__init__(f"HCaptcha Solver API: {code} (HTTP {status})");self.status=status;self.code=code;self.idempotency_key=idempotency_key
