# Turn14 Shopify Inventory
This is a script to update your Shopify Inventory with Turn14.com's inventory every hour (the time interval they use to update their inventory spreadsheet).  

I made this before Turn14.com released their REST API, but I feel this is still useful to those who do not have experience with APIs.

## Dependencies
__Please note that this uses MySQL, make sure you have that installed before installing dependencies but you can use whatever db you are comfortable with__
1. Shopify __Use `pip install ShopifyAPI` if you aren't using MySQL__
1. MySQL-python  
### Installing Dependencies
Simply run the following command:
```python
pip install -r requirements.txt
```

## Turn14 Credentials
Please be sure to update turn14_creds.json where **`"username": "username",`** to your username and **`"password": "password"`** to your password.