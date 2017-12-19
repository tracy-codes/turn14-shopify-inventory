import shopify
import csv
import MySQLdb
import sys
import time
import requests
from zipfile import ZipFile
import glob
import os
from os.path import join

def download_file():
    s = requests.session()
    login_data = {'password':'rumblebros', 'username':'rumblebros'}
    s.post('https://www.turn14.com/user/login', data=login_data)
    zipurl = 'https://www.turn14.com/export.php?action=inventory_feed'
    resp = s.get(zipurl)
    zname = 'inventory.zip'
    zfile = open(zname, 'wb')
    zfile.write(resp.content)
    zfile.close()

def unzip_file():
    zip = ZipFile('inventory.zip')
    zip.extractall()


# sys.setdefaultencoding() does not exist, here!
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

shop_url = "https://%s:%s@rumblebros.myshopify.com/admin" % ("c9acdeda24dce98f7c0832bec66cfa86", "c4fe01abe7a8265d29aa38f25caa70ee")
shopify.ShopifyResource.set_site(shop_url)
shop = shopify.Shop.current()

conn = MySQLdb.connect("localhost","root","cookies","test")

c = conn.cursor()

c.execute("SELECT * FROM inv")

rows = c.fetchall()

def update_inventories():
    list_of_files = glob.glob('*.csv') # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)
    latest_file
    csv_file = list(csv.reader(open(latest_file, "r"), delimiter=","))
    api_limit = 0
    for row in rows:
        db_id = str(row[1])
        sku = str(row[2])
        stock = int(row[3])
        #print(db_id, sku, stock)
        for b in csv_file:
            if sku in b[0]:
                new = int(b[4])
                c.execute("UPDATE inv SET inventory=%s where sku=%s",(str(new), str(sku)))
                conn.commit()
                print "Updated inventory for %s in db from %s to %s!" % (db_id, str(stock),str(new))
                product = shopify.Variant.find(db_id)
                old_prod_inv = product.inventory_quantity
                if api_limit < 40:
                    product.inventory_quantity = new
                    product.save()
                    api_limit = api_limit+1
                    print "\033[1;36mInventory for SKU \033[1;35m%s \033[1;36mhas been updated from \033[1;31m%s \033[1;36mto \033[1;32m%s\033[1;36m!'\033[1;37m" % (str(sku), str(old_prod_inv), str(new))
                else:
                    print"\033[1;31mAPI Limit Reached, waiting 20 seconds...'\033[1;37m"
                    time.sleep(20)
                    api_limit = 0
                    continue

def get_all_resources(resource, **kwargs):
    resource_count = resource.count(**kwargs)
    resources = []
    if resource_count > 0:
        for page in range(1, ((resource_count-1) // 250) + 2):
            kwargs.update({"limit" : 250, "page" : page})
            resources.extend(resource.find(**kwargs))
    return resources

def add_to_db():
    product_ids = get_all_resources(shopify.Product)
    for a in product_ids:
        ven = ['T14', 'Invidia', 'Perrin', 'Rally Armor', 'Mishimoto']
        for b in a.variants:
            x = b.id
            y = b.sku
            z = b.inventory_quantity
            c.execute("SELECT prod_id FROM inv WHERE prod_id = %s", (x))
            db_row_count = c.rowcount
            for v in ven:
                if a.vendor == v:
                    print v
                    if db_row_count == 0:
                        if y:
                            if "ASP" not in y:
                                if y not in rows:
                                    c.execute("INSERT INTO inv (prod_id, sku, inventory) VALUES (%s, %s, %s)",(str(x), str(y), int(z)))
                                    conn.commit()
                                    print "added %s to the database" % a.id
                    else:
                        continue


def remove_used():
    dir = "./"
    test = os.listdir(dir)
    for item in test:
        if item.endswith('.zip'):
            os.remove(join(dir,item))
        if item.endswith('.csv'):
            os.remove(join(dir,item))

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
        print('Removing old files...')
        remove_used()
        print("Old files have been removed...")
        print('Next task is scheduled for 1 hour')
        time.sleep(3600)
