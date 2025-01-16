from django.db import models
import random
import string
# Create your models here.

# Create your models here.
class Userdata(models.Model):
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
    user_passphrase = models.CharField(max_length=100, null=True, blank=True)
    user_signal_on = models.BooleanField(default=0)
    user_tradingview_url = models.TextField(null=True,blank=True)


    def save(self, *args, **kwargs):
        if not self.user_passphrase:  # Generate passphrase only if not already set
            self.user_passphrase = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.user_email

    class Meta:
        db_table = 'Userdata'


class User_Preference(models.Model):
    user_preference = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(Userdata, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=100, null=True, blank=True)
    order_size = models.IntegerField(null=True, blank=True)
    time_in_force = models.CharField(max_length=100, null=True, blank=True)
    order_type = models.CharField(max_length=100, null=True, blank=True)
    account = models.CharField(max_length=100,null=True,blank=True)
    # marketorder
    # limitorder
    # stoplosslimitorder
    # takemultipleprofitorder

    def __str__(self):
        return self.user_id.user_email

    class Meta:
        db_table = 'User_Preference'


class Access_Token(models.Model):
    Access_Token_id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(Userdata, on_delete=models.CASCADE)
    access_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    expiry_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user_id.user_email

    class Meta:
        db_table = 'Access_Token'




class multiple_take_profit_orders(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(Userdata, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    order_id = models.BigIntegerField()

    def __str__(self):
        return self.user_id.user_email

    class Meta:
        db_table = 'multiple_take_profit_orders'




class calender_data(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    Datetimee = models.DateTimeField(null=True,blank=True)
    Event_Start = models.DateTimeField(null=True,blank=True)
    Event_End = models.DateTimeField(null=True,blank=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    impact = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.title, self.Datetimee)

    class Meta:
        db_table = 'calender_data'