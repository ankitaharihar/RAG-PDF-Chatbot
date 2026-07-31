from services.email_service import send_test_email

email = input("Enter your email: ")

success, message = send_test_email(email)

print("Success:", success)
print("Message:", message)