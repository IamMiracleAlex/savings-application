from django.db import models

# Create your models here.
class KYCProfile(models.Model):
	LEVEL_0, LEVEL_1, LEVEL_2 = range(3)

	KYC_LEVEL = (
		(LEVEL_0, 'LEVEL 0'),
		(LEVEL_1, 'LEVEL 1'),
		(LEVEL_2, 'LEVEL 2')
	)
	user = models.OneToOneField(
		'users.CustomUser', 
		on_delete=models.CASCADE, 
		null=True, 
		blank=True
	)
	bvn = models.CharField(max_length=11, unique=True, blank=True, null=True)
	name = models.CharField(max_length=150, blank=True, null=True)
	phone_number = models.CharField(max_length=15, blank=True, null=True)
	dob = models.CharField(max_length=15, blank=True, null=True)
	verification_level = models.PositiveSmallIntegerField(
		choices=KYC_LEVEL,
		default=LEVEL_0
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return "{} {} LEVEL: {}".format(self.user.first_name, self.user.last_name, self.verification_level)