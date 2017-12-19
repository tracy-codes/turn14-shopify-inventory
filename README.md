# Turn14 Shopify Inventory
This is a script to update your Shopify Inventory with Turn14.com's inventory every hour (the time interval they use to update their inventory spreadsheet).  

I made this before Turn14.com released their REST API, but I feel this is still useful to those who do not have experience with APIs.

## Dependencies
**Please note that this uses MySQL, make sure you have that installed before installing dependencies but you can use whatever db you are comfortable with.**
1. [Shopify](https://github.com/Shopify/shopify_python_api) **Use `pip install ShopifyAPI` if you aren't using MySQL**
1. MySQL-python  
### Installing Dependencies
Simply run the following command:
```python
pip install -r requirements.txt
```

## Turn14 Credentials
Please be sure to update turn14_creds.json where **`"username": "username"`** to your username and **`"password": "password"`** to your password.

## Shopify API
- You will need to create a private app in your dashboard
  - Follow this tutorial: [Generate private API credentials](https://help.shopify.com/api/getting-started/api-credentials#generate-private-api-credentials)
  - You will need to assign Read and Write access to "read_products, write_products" in your admin dashboard
- You will need to update **`shop_name="your shop name"'`** to your shop's name (i.e. yourshopname in yourshopname.myshopify.com)
- You will also neeed to update **`"api_key": "your api key"`** and **`"api_pass": "your api password"`** to your 