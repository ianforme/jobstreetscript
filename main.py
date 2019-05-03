from process import initialise_driver, login, search_keyword, extract_data, next_page, create_folder, send_email
import config
import pandas as pd
import datetime
import os

# read in system information and jobstreet.com credentials
driver_path = config.driver_path
url = config.url
username = config.username
password = config.password
keywords = config.keywords
pages = config.pages
data_path = config.data_path
today = datetime.datetime.now().strftime("%Y%m%d")

# Create folder
data_path = create_folder(data_path, today)

# Initialise and login to jobstreet.com
driver = initialise_driver(url, driver_path)
driver = login(driver, username, password)

try:
    # Extract results
    for kwd in keywords:
        # For each keyword, create a CSV file
        result_df = pd.DataFrame(columns=['job_title', 'company', 'location', 'salary', 'description', 'recency', 'url'])
        driver = search_keyword(driver, kwd)

        # For each page, do extraction, then go to next page
        for _ in range(pages):
            driver, res_df = extract_data(driver)
            driver = next_page(driver)
            result_df = pd.concat([result_df, res_df])
        # Save results to csv
        result_df.to_csv(os.path.join(data_path, "{}_{}.csv".format(kwd, today)), index=False)

    driver.close()
    flag = 0
except:
    flag = 1

# Now for the email
sender_email = config.email_sender
sender_password = config.sender_password
receiver_email = config.email_receiver
subject = "{} Jobs from Jobstree.com".format(today)
body = """
Hi,

Here is a summary for the day:

TODO

"""
send_email(flag, sender_email, sender_password, receiver_email, subject, body, data_path)

