# Piggy Bank Program
- Two types of customers: ADMIN or Customer
- Default users: admin, piggy1, piggy2
- Ability to create new users as admin
- Ability to initialize system as admin

# How to get Started
## Set up System
1. start program: python bank.py
```
This is the Piggy Bank Accounting System Program.
Administrator can reset system via initialize action.
Customer actions: deposit, withdrawl, transfer, create new account.

Please choose who you are:
0:ADMINISTRATOR
1:CUSTOMER
2:HELP
3:EXIT
```   
2. log in as "administrator" selecting option 0 with password "1234"
```
Select an action:
0:RESTART
1:INITIALIZE
2:NEWUSER
3:USERLIST
```
3. select "Initilize" option
4. log out

### Admin Actions
1. initialize - creates underlying data system requires to start up
2. all users list - view all user names
3. restart - ignore for now
4. create new user

## Access Customer Actions
1. log in as a customer, piggy1 or pigggy2 and use pin 1234
```
Please choose who you are:
0:ADMINISTRATOR
1:CUSTOMER
2:HELP
3:EXIT
=> 1
Please enter user name:
=> piggy1
Please enter the access code:
=> 1234
Please select a customer action:
0:OPEN
1:DEPOSIT
2:WITHDRAW
3:TRANSFER
4:BALANCE
```
### Customer Actions
1. deposit - adds money to a selected account
2. withdrawl - remvoews money from a selected account
3. open - opens new account
4. transfer - move money from one user account to another

# Additional Details
- all defualt pins are "1234"
- as admin you can create new users
