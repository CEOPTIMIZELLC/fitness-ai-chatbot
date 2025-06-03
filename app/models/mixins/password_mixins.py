import re
from app import db, bcrypt

# Make sure that the passwords match.
def do_passwords_match(password1, password2):
    return password1 == password2

# Make sure that inputted password follows desired format. Flag if invalid.
def is_password_valid(password):
    # Make sure password is between 
    if (len(password)<8) or (len(password)>20):
        return "Password must be between 8 and 20 letters long."
    # Make sure password has at least one number
    elif not re.search("[0-9]", password):
        return "Password must have at least one number."
    # Make sure password has at least special character
    elif not re.search("[!@#$%\^&*_\?+=]", password):
        return "Password must have at least one of the following characters [!@#$%^&*_?]."
    else: 
        return None

class PasswordMixin(db.Model):
    __abstract__ = True
    password_hash = db.Column(db.String, nullable=False)

    def set_password(self, password, password_confirm):
        # Make sure that both passwords match.
        if not do_passwords_match(password, password_confirm):
            return "Passwords should match!"

        # Make sure that the password is in a valid format.
        password_flag = is_password_valid(password)
        if password_flag: 
            return password_flag

        # If input password has passed all tests, set the password.
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        return None

    # Make sure password matches
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)