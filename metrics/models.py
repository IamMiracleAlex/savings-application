from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Metric(models.Model):
	total_deposits = models.IntegerField(default=0)
	total_deposits_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	total_paystack_deposits = models.IntegerField(default=0)
	total_paystack_deposits_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	total_monnify_deposits = models.IntegerField(default=0)
	total_monnify_deposits_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	total_chicken_change_deposits = models.IntegerField(default=0)
	total_chicken_change_deposits_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	total_withdraws = models.IntegerField(default=0)
	total_withdraws_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	total_transfers = models.IntegerField(default=0)
	total_transfers_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	wallet_balance = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	autosave_balance = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	target_balance = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	total_payments = models.IntegerField(default=0)
	total_payments_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	total_accounts_with_interests = models.IntegerField(default=0)
	activated_users_count = models.IntegerField(default=0)
	total_interests_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	total_interests_for_today = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	bill_payment_fees_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	autosave_breaking_fees_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	wallet_autosave_transfer_count = models.IntegerField(default=0)
	wallet_autosave_transfer_sum = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	autosave_wallet_transfer_count = models.IntegerField(default=0)
	autosave_wallet_transfer_sum = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	wallet_target_transfer_count = models.IntegerField(default=0)
	wallet_target_transfer_sum = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	target_wallet_transfer_count = models.IntegerField(default=0)
	target_wallet_transfer_sum = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	wallet_wallet_transfer_count = models.IntegerField(default=0)
	wallet_wallet_transfer_sum = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
		)
	referral_bonus_total = models.IntegerField(default=0)
	referral_bonus_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
	)
	airtime_bonus_total = models.IntegerField(default=0)
	airtime_bonus_volume = models.DecimalField(default=0.00,
		decimal_places=2,
		max_digits=12,
	)
			

	new_users =  models.IntegerField(default=0)
	referrals =  models.IntegerField(default=0)
	start_date = models.DateField(blank=True, null=True)
	end_date = models.DateField(blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)


   