# Piggy Bank Program
This is the Piggy Bank Accounting System Program.   
There two main actors:
- Administrator who can initialize action, see all users, or create new users.
- Customer who can deposit money, withdrawl money, or transfer money, and create new account.

The default users are admin, piggy1, and piggy2.

# How to get Started
## Set up System
1. start program => python bank.py
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
3. select "INITIALIZE" option
4. log out

### Admin Actions
0. RESTART - Ignore for now
1. INITIALIZE - creates underlying data system requires to start up
2. NEWUSER - create new user
3. USERLIST - view all user names

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
1. DEPOSIT - adds money to a selected account
2. WITHDRAWL - remvoews money from a selected account
3. OPEN - opens new account
4. TRANSFER - move money from one user account to another

# Additional Details
- all defualt pins are "1234"
- as admin you can create new users
