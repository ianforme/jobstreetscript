from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import smtplib
import os

def initialise_driver(url, path):
    """
    Initialise the chrome driver

    :param url: jobstreet url
    :param path: driver path
    :return: webdriver
    """

    # Initialise the driver
    chrome_options = webdriver.ChromeOptions()

    # This setting prevent website from sending notifications
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(path, chrome_options=chrome_options)

    # Target URL
    url = "https://myjobstreet.jobstreet.com.sg/home/login.php"
    driver.get(url)

    return driver

def login(driver, username, password):
    """
    Simulate login account

    :param driver: webdriver
    :param username: jobstreet username
    :param password: jobstreet password
    :return: driver: webdriver
    """
    # Simulate login
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "login_id"))
    ).send_keys(username)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "password"))
    ).send_keys(password)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "btn_login"))
    ).click()

    return driver

def search_keyword(driver, keyword):
    """
    Search by keywords

    :param driver: webdriver
    :param keyword: job title / keywords
    :return: webdriver
    """
    first_keyword = keyword
    driver.find_element_by_id("search_box_keyword").clear()
    driver.find_element_by_id("search_box_keyword").send_keys(first_keyword)
    driver.find_element_by_id("header_searchbox_btn").click()

    return driver

def extract_data(driver):
    """
    For each job posted, extract:
        - job title
        - company
        - location
        - salary
        - description
        - post dates
        - url

    :param driver: webdriver
    :return: list of webdriver and data frame
    """
    # Extract all the displayed components + and all the relevant panels on the webpage
    panels = driver.find_elements_by_xpath("//div[not(contains(@style,'display:none'))]/div[@id[starts-with(.,'job_ad_')]]")

    # Create result dictionary
    res_dict = {
        'job_title': [],
        'company': [],
        'location': [],
        'salary': [],
        'description': [],
        'recency': [],
        'url': [],
    }

    # for each panel, extract relevant information
    for i, panel in enumerate(panels):

        # For job title and url
        try:
            title = panel.find_element_by_class_name('position-title-link').text
            url = panel.find_element_by_class_name('position-title-link').get_attribute('href')

        except:
            title = None
            url = None

        # For company name
        try:
            company = panel.find_element_by_class_name('company-name').text
        except:
            company = None

        # For location
        try:
            location = panel.find_element_by_class_name('job-location').text
        except:
            location = None

        # For expected salary
        try:
            salary = panel.find_element_by_class_name('expected-salary').text
        except:
            salary = None

        # For description
        try:
            description = panel.find_element_by_id('job_desc_detail_{}'.format(i+1)).text
        except Exception as e:
            print(e)
            description = None

        # For post dates
        try:
            recency = panel.find_element_by_id('posted_datetime_{}'.format(i+1)).text
        except:
            recency = None

        # aggregate results
        res_dict['job_title'].append(title)
        res_dict['company'].append(company)
        res_dict['location'].append(location)
        res_dict['salary'].append(salary)
        res_dict['description'].append(description)
        res_dict['recency'].append(recency)
        res_dict['url'].append(url)

    res_df = pd.DataFrame(res_dict)

    return [driver, res_df]

def next_page(driver):
    """
    Navigate to next page

    :param driver: webdriver
    :return: webdriver
    """

    driver.find_element_by_id("page_next").click()

    return driver

def create_folder(path, date):
    """
    Create folder to store extracted data

    :param path: folder path
    :param date: date
    :return: path of folder createed
    """

    if not os.path.isdir(path):
        os.mkdir(path)

    res_dir = os.path.join(path, date)
    if not os.path.isdir(res_dir):
        os.mkdir(res_dir)

    return res_dir

def send_email(flag, sender_email, sender_password, receiver_email, subject, body, attachement_path):
    """
    Send results to an email

    :param flag: flag of success or fail of extraction
    :param sender_email: sender's email
    :param sender_password: sender's password
    :param receiver_email: receivers email
    :param subject: email subject
    :param body: email body
    :param attachement_path: path for all attachements are stored
    :return: None
    """
    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(sender_email, sender_password)

    if flag == 0:
        # instance of MIMEMultipart
        msg = MIMEMultipart()

        # storing the sender and receiver email address
        msg['From'] = sender_email
        msg['To'] = receiver_email

        # storing the subject and body
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # open the file to be sent
        for file in os.listdir(attachement_path):
            file = os.path.join(attachement_path, file)
            attachment = open(file, "rb")

            # instance of MIMEBase and named as p
            p = MIMEBase('application', 'octet-stream')
            p.set_payload((attachment).read())
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', "attachment; filename= %s" % file)

            # attach the instance 'p' to instance 'msg'
            msg.attach(p)

        text = msg.as_string()
    else:
        text = "Error Happened"

    # send email
    s.sendmail(sender_email, receiver_email, text)
    # terminating the session
    s.quit()
