from flask_bcrypt import Bcrypt
b = Bcrypt()
print(b.generate_password_hash('user123').decode('utf-8'))