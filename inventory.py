import shopify
import csv
#import MySQLdb
import sys
import time
import requests
from zipfile import ZipFile
import glob
import os
from os.path import join
import json

# load config file
config = json.load(open("config.json"))

# shopify credentials
SHOP_NAME = config['shopify'][0]['shop_name']
API_KEY = config['shopify'][0]['api_key']
API_PASS = config['shopify'][0]['api_pass']

# sets shop url
shop_url = "https://%s:%s@%s.myshopify.com/admin" % (API_KEY, API_PASS, SHOP_NAME)
shopify.ShopifyResource.set_site(shop_url)
shop = shopify.Shop.current()

# your db information
db_host = config['database'][0]['host']
db_username = config['database'][0]['username']
db_password = config['database'][0]['password']
db_schema = config['database'][0]['schema']
conn = MySQLdb.connect(db_host, db_username, db_password, db_schema)
c = conn.cursor()
c.execute("SELECT * FROM inv")
rows = c.fetchall()

# turn14 credentials
t14_username = config['turn14'][0]['username']
t14_password = config['turn14'][0]['password']

# downloads inventory spreadsheet from turn14.com
def download_file():
    # initiates requests session
    s = requests.session()
    # set login data
    login_data = {'password':t14_password, 'username':t14_username}
    # posts login to turn14.com
    s.post('https://www.turn14.com/user/login', data=login_data)
    # url for inventory update csv
    zipurl = 'https://www.turn14.com/export.php?action=inventory_feed'
    # downloads zip file as inventory.zip
    resp = s.get(zipurl)
    zname = 'inventory.zip'
    zfile = open(zname, 'wb')
    zfile.write(resp.content)
    zfile.close()
    # unzips file
    unzip_file()

# unzips file
def unzip_file():
    print "Unzipping inventory.zip"
    zip = ZipFile('inventory.zip')
    zip.extractall()

reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

# updates shopify and db
def update_inventories():
    # gets latest file (i.e. inventory file)
    list_of_files = glob.glob('*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)
    latest_file
    csv_file = list(csv.reader(open(latest_file, "r"), delimiter=","))
    # track api limit
    api_limit = 0
    # loops through all rows of db
    for row in rows:
        # shopify product id
        db_id = str(row[1])
        # product sku
        sku = str(row[2])
        # inventory count
        stock = int(row[3])
        # loops through rows of inventory file
        for b in csv_file:
            # checks to see if sku matches current row
            if sku in b[0]:
                # get new inventory
                new = int(b[4])
                # set db inventory to new inventory
                c.execute("UPDATE inv SET inventory=%s where sku=%s",(str(new), str(sku)))
                conn.commit()
                print "Updated inventory for %s in db from %s to %s!" % (db_id, str(stock),str(new))
                # update shopify inventory to new inventory
                product = shopify.Variant.find(db_id)
                old_prod_inv = product.inventory_quantity
                # continue if rate limit hasn't been reached
                if api_limit < 40:
                    product.inventory_quantity = new
                    product.save()
                    api_limit = api_limit+1
                    print "\033[1;36mInventory for SKU \033[1;35m%s \033[1;36mhas been updated from \033[1;31m%s \033[1;36mto \033[1;32m%s\033[1;36m!'\033[1;37m" % (str(sku), str(old_prod_inv), str(new))
                # wait for 20s to let Shopify's rate bucket empty
                else:
                    print"\033[1;31mAPI Limit Reached, waiting 20 seconds...'\033[1;37m"
                    time.sleep(20)
                    api_limit = 0
                    continue

# fix for pagination on Shopify's end
# allows us to get more than 250 products
def get_all_resources(resource, **kwargs):
    resource_count = resource.count(**kwargs)
    resources = []
    if resource_count > 0:
        for page in range(1, ((resource_count-1) // 250) + 2):
            kwargs.update({"limit" : 250, "page" : page})
            resources.extend(resource.find(**kwargs))
    return resources

# adds new products that aren't in db to db
def add_to_db():
    product_ids = get_all_resources(shopify.Product)
    for a in product_ids:
        # replace ven list to the vendors you want to check for in Shopify
        ven = ['T14', 'Invidia', 'Perrin', 'Rally Armor', 'Mishimoto']
        # loops through all product variants
        for b in a.variants:
            # shopify product id
            x = b.id
            # shopify product sku
            y = b.sku
            # shopify product inventory
            z = b.inventory_quantity
            # gets all variants of product_id in db
            c.execute("SELECT prod_id FROM inv WHERE prod_id = %s", (x))
            db_row_count = c.rowcount
            # loops through vendors
            for v in ven:
                # checks to see if shopify product vendor matches vendor we're looking for
                if a.vendor == v:
                    # checks to see if shopify product id is in db or not
                    if db_row_count == 0:
                        # checks to see if product has a sku (products we aren't looking for won't have a sku)
                        if y:
                            # checks to see if product is not of a certain type, you may remove this if you want
                            if "ASP" not in y:
                                # doublechecks to make sure sku is not in db one last time
                                if y not in rows:
                                    # inserts new product to db
                                    c.execute("INSERT INTO inv (prod_id, sku, inventory) VALUES (%s, %s, %s)",(str(x), str(y), int(z)))
                                    conn.commit()
                                    print "added %s to the database" % a.id
                    else:
                        continue

# removes .zip and .csv files
def remove_used():
    dir = "./"
    test = os.listdir(dir)
    for item in test:
        if item.endswith('.zip'):
            os.remove(join(dir,item))
        if item.endswith('.csv'):
            os.remove(join(dir,item))

# main method to loop infinitely every hour
if __name__ =='__main__':
    while True:
        print "Updating DB"
        add_to_db()
        print "Downloading new csv"
        download_file()
        print "Unzipping new csv"
        unzip_file()
        time.sleep(5)
        print "Updating inventories"
        update_inventories()
        print "Removing old files..."
        remove_used()
        print "Old files have been removed..."
        print"Next task is scheduled for 1 hour"
        time.sleep(3600)
