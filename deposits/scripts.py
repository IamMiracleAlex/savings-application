from .models import FundSource
def sanitize_users():
	for fund_source in FundSource.objects.all():
		similar_cards = FundSource.objects.filter(last4=fund_source.last4, bank_name=fund_source.bank_name, exp_month=fund_source.exp_month, exp_year=fund_source.exp_year)
		if similar_cards.count() > 1:
				for card in similar_cards:
						user = card.user
						user.is_active=False
						user.save()
				user = fund_source.user
				user.is_active=False
				user.email
				user.save()



