import requests

from decouple import config

BASE_URL = config('PAYSTACK_BASE_URL')
PAYSTACK_KEY = config('PAYSTACK_KEY')


class PaystackService:

	def initialize_transaction(self, amount, email):
		''' Used for initializing a transaction.
			Accepts - email, and amount.
			Returns - authorization_url, access_code, reference, status, message
		'''

		header = {'Authorization': f'Bearer {PAYSTACK_KEY}'}
		payload = {'amount': amount, 'email': email }

		resp = requests.post(f'{BASE_URL}/transaction/initialize',
							data = payload,
							headers = header, 
							).json()
		return resp


	def resolve_account_number(self, account_number, bank_code):
		''' Used to verify an account number.
			Accepts - account number and bank code.
			Returns - account_number, account_name, bank_id
		'''

		header = {'Authorization': f'Bearer {PAYSTACK_KEY}'}

		resp = requests.get(f'{BASE_URL}/bank/resolve?account_number={account_number}&bank_code={bank_code}',
							headers = header, 
							).json()
		return resp		


	def create_transfer_recipient(self, user, account_no, bank_code):
		path = '/transferrecipient/'
		response = requests.post(
			(BASE_URL + path),
			data = {'type': 'nuban', 'name': user.full_name(), 'account_number': account_no, 'bank_code': bank_code },
			headers = {'Authorization': "Bearer {}".format(PAYSTACK_KEY)}
		).json()
		
		return response
	
	def transfer(self, withdraw):
		path = '/transfer'
		user = withdraw.account.user
		amount = int(withdraw.amount) * 100
		recipient_code = user.default_withdraw_beneficiary.recipient_code
		return post_request(path, {
			'source': 'balance', 
			'amount': amount, 
			'recipient': recipient_code, 
			'reference': withdraw.reference,
			'reason': withdraw.reference 
		})

	def verify_transaction(self, reference):
		path = '/transaction/verify/'
		response = requests.get(
			(BASE_URL+path+reference),
			headers = {'Authorization': "Bearer {}".format(PAYSTACK_KEY)}
			).json()
		return response

	def charge_card(self, deposit, fund_source):
		path = '/transaction/charge_authorization/'
		amount = int(deposit.amount) * 100
		return post_request(path, {
			'amount': amount, 
			'email': fund_source.user.email, 
			'authorization_code': fund_source.auth_code, 
			'reference': deposit.reference
		})
	
	def verify_bvn(self, bvn):
		path = "/bank/resolve_bvn/{}".format(bvn)
		response = requests.get(
			(BASE_URL+path),
			headers = {'Authorization': "Bearer {}".format(PAYSTACK_KEY)}
			).json()
		return response

def post_request(path, data):
	response = requests.post(
		(BASE_URL+path),
		data = data,
		headers = {'Authorization': "Bearer {}".format(PAYSTACK_KEY)}
	).json()
	return response