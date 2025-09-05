import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException


EMAIL = ""
PASSWORD = ""
GYM_URL = "https://appbrewery.github.io/gym/"


user_data_directory = os.path.join(os.getcwd(), "chrome_profile")

if not os.path.exists(user_data_directory):
    os.makedirs(user_data_directory)


chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument(f"--user-data-dir={user_data_directory}")


driver = webdriver.Chrome(options=chrome_options)
driver.get(GYM_URL)
wait = WebDriverWait(driver,2)

def retry(func, retries=7, description=None):
    for i in range(retries):
        print(f"Trying {description}, Attempt: {i +1}")
        try:
            return func()
        except TimeoutException:
            if i == retries - 1:
                raise
            time.sleep(1)


def log_in():
    log_in = wait.until(ec.element_to_be_clickable((By.ID, "login-button")))
    log_in.click()

    email_btn = wait.until(ec.element_to_be_clickable((By.ID, "email-input")))
    email_btn.clear()
    email_btn.send_keys(EMAIL)

    password = driver.find_element(By.ID, "password-input")
    password.clear()
    password.send_keys(PASSWORD)

    submit = driver.find_element(By.ID, "submit-button")
    submit.click()
    wait.until(ec.presence_of_element_located((By.ID, "schedule-page")))

booked_count = 0
waitlist_count = 0
already_booked_count = 0


class_cards = driver.find_elements(By.CSS_SELECTOR, "div[id^='class-card-']")

processed_classes = []
for card in class_cards:
    day_group = card.find_element(By.XPATH, "./ancestor::div[contains(@id, 'day-group-')]")
    day_title = day_group.find_element(By.TAG_NAME, "h2").text
    if "Tue" in day_title or "Thu" in day_title:
        time_text = card.find_element(By.CSS_SELECTOR, "p[id^='class-time-']").text
        if "6:00 PM" in time_text:
            # Get the class name
            class_name = card.find_element(By.CSS_SELECTOR, "h3[id^='class-name-']").text
            class_info = f"{class_name} on {day_title}"

            # Find the book button
            button = card.find_element(By.CSS_SELECTOR, "button[id^='book-button-']")

            if "Booked" in button.text:
                print(f"Already booked: {class_name}, {day_title}")
                already_booked_count+=1
                processed_classes.append(f"[Booked] {class_info}")

            elif "Waitlisted" in button.text:
                print(f"Already on waitlist: {class_name}, {day_title}")
                already_booked_count+=1
                processed_classes.append(f"[Waitlisted] {class_info}")
            elif "Join Waitlist" in button.text:
                button.click()
                print(f"Joined Waitlist: {class_name}, {day_title}")
                processed_classes.append(f"[New Waitlist] {class_info}")
                waitlist_count+=1
            elif "Book Class" in button.text:
                button.click()
                print(f"✓ Booked: {class_name} on {day_title}")
                booked_count += 1
                processed_classes.append(f"[New Booking] {class_info}")

expected = booked_count + waitlist_count + already_booked_count
print(f"\nTotal Tuesday and Thursday 6pm classes processed: {expected}\n\n")

print("--- VERIFYING ON MY BOOKINGS PAGE ---")

bookings_page = driver.find_element(By.ID, "my-bookings-link")
bookings_page.click()

wait.until(ec.presence_of_element_located((By.ID, "my-bookings-page")))

bookings = 0
all_cards = driver.find_elements(By.CSS_SELECTOR, "div[id*='card-']")

for card in all_cards:
    try:
        when_paragraph = card.find_element(By.XPATH, ".//p[strong[text()='When:']]")
        when_text = when_paragraph.text

        # Check if it's a Tuesday or Thursday 6pm class
        if ("Tue" in when_text or "Thu" in when_text) and "6:00 PM" in when_text:
            class_name = card.find_element(By.TAG_NAME, "h3").text
            print(f"  ✓ Verified: {class_name}")
            bookings += 1
    except NoSuchElementException:
        # Skip if no "When:" text found (not a booking card)
        pass

difference = expected - bookings


print("\n--- VERIFICATION RESULT ---")
print(f"Expected: {expected} bookings")
print(f"Found: {bookings} bookings")
if expected == bookings:
    print("✅ SUCCESS: All bookings verified!")
else:
    print(f"❌ MISMATCH: Missing {difference} bookings")


driver.quit()

