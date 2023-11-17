import json

def setup_user_details():
    user_details = {}
    user_details['full_name'] = input("Enter your full name: ")
    user_details['email'] = input("Enter your email address: ")

    with open("user_details.json", "w") as file:
        json.dump(user_details, file, indent=4)
    
    print("User details saved successfully.")

if __name__ == "__main__":
    setup_user_details()
