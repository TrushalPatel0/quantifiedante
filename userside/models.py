from django.db import models

# Create your models here.

# Create your models here.
class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    user_name = models.CharField(max_length=155)
    user_email = models.EmailField()
    user_contact = models.CharField(max_length=15, null=True, blank=True)
    user_password = models.CharField(max_length=55)
    user_otp = models.CharField(max_length=6, null=True, blank=True)
    user_dob = models.DateField(null=True, blank=True)
    user_gender = models.CharField(max_length=15, null=True, blank=True)
    user_ack = models.BooleanField(default=1, null=True, blank=True)
    user_address = models.TextField(null=True, blank=True)
    user_passphrase = models.CharField(max_length=100, null=True,blank=True)
    user_signal_on = models.BooleanField(default=0)

    def __str__(self):
        return self.user_email

    class Meta:
        db_table = 'User'


class User_Preference(models.Model):
    user_preference = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=100, null=True, blank=True)
    order_size = models.IntegerField(null=True, blank=True)
    time_in_force = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.user_id.user_email

    class Meta:
        db_table = 'User_Preference'


class Access_Token(models.Model):
    user_preference = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    expiry_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user_id.user_email

    class Meta:
        db_table = 'Access_Token'

