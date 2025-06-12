from app import db
from email_validator import validate_email, EmailNotValidError

# Make sure that the email is in the desired format. Flag if invalid.
def is_email_valid(email):
    try:
        v = validate_email(email)
        # Return normalized form
        email = v.email
        return email, True
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        return str(e), False

class EmailMixin(db.Model):
    __abstract__ = True
    email = db.Column(db.String(120), unique=True, nullable=False)

    def set_email(self, email):
        # Make sure that email is in a valid format.
        email, email_valid = is_email_valid(email)
        if not email_valid: 
            return email
        self.email = email
        return None

# Testing the script
if __name__ == '__main__':
    print("== Email Tests ==")
    print(is_email_valid("abercrombe@gmail.com"))
    print(is_email_valid("@bercrombe@gmail.com"))
    print(is_email_valid("@gmail.com"))
    print(is_email_valid(""))
    print(is_email_valid("abercrombe@gmail.com"))
