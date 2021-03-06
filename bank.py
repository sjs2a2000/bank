import json
import sys
import os
import logging
import shutil
import tempfile
import getpass

'''
README:
Currently program does the following:
1. creates user file in /tmp/user098/users/ for ex. /tmp/user098/users/piggy1
2. creates accounts in /tmp/user098/accounts/ for ex. /tmp/user098/accounts/xx1
3.creates a maxaccount file to track the account numbers

the program has three classes: BankSystem, User, BankAccount
the program saves all data to the files
the program has locking allowing for multiple users to access the db

The main issue below is we don't record all the transactions nor to we manage all transactions atomically

TODO:
1. record all transaction changes tracking balance
2. read last record rather then single record in account file
The above steps would make the program hardened against failure
3. add more tests
4. encrypt passwords
'''
logging.basicConfig()
#console = logging.StreamHandler()
logger = logging.getLogger(__name__)
logger.info('Starting logger for...') 
#console = logging.StreamHandler()
#logger.addHandler(console)

TEMPDIR=""
if os.name=='nt':
    TEMPDIR=os.path.join(tempfile.gettempdir(),getpass.getuser())
else:
    TEMPDIR=os.path.join(tempfile.gettempdir(),os.getlogin())
   
                         
if not os.path.exists(TEMPDIR):
    os.makedirs(TEMPDIR)


#enums
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums['reverse_mapping'] = reverse    
    #print enums
    return( type('Enum', (), enums))

#file locking
if os.name == 'nt':
    import win32con, win32file, pywintypes
    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0 # the default
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    _overlapped = pywintypes.OVERLAPPED(  )
    class Lock(object):
        # needs win32all to work on Windows 
        @staticmethod
        def lockf(file, flags):
            hfile = win32file._get_osfhandle(file.fileno(  ))
            win32file.LockFileEx(hfile, flags, 0, 0xffff0000, _overlapped)
        
        @staticmethod
        def unlockf(file):
            hfile = win32file._get_osfhandle(file.fileno(  ))
            win32file.UnlockFileEx(hfile, 0, 0xffff0000, _overlapped)
elif os.name == 'posix':
    import fcntl
    from fcntl import LOCK_EX, LOCK_SH, LOCK_NB
    class Lock(object):
        @staticmethod
        def lockf(file, flags):
            fcntl.flock(file.fileno(  ), flags)

        @staticmethod
        def unlockf(file):
            fcntl.flock(file.fileno(  ), fcntl.LOCK_UN)
else:
    raise RuntimeError("only defined for nt and posix platforms")

class FileStore(object):    
    USER_DIR = os.path.join(TEMPDIR,'users')
    ACCOUNT_MAX = os.path.join(TEMPDIR,'max_account.json')
    ACCOUNT_DIR=os.path.join(TEMPDIR,'accounts')
    
    def __init__(self):
        self.locker=Lock()

    def read(self, filename, uselock=False):       
        with open(filename) as infile:
            if uselock:
                self.locker.lockf(infile, LOCK_SH )
            data = json.load(infile)
            if uselock:
                self.locker.unlockf(infile)
        return data
        
    def write(self, filename, data, uselock=False, **kwargs):        
        with open(filename, 'w') as outfile:
            if uselock:
                self.locker.lockf(outfile,LOCK_EX)
            json.dump(data, outfile)
            if uselock:
                self.locker.unlockf(outfile)
        return True
    
    def remove_all(self):
        for dest in [self.USER_DIR, self.ACCOUNT_DIR, self.ACCOUNT_MAX]:
            shutil.rmtree(dest, ignore_errors=True)        
        os.makedirs(self.USER_DIR)
        os.makedirs(self.ACCOUNT_DIR)
    
class BankAccount(object):
    def __init__(self, name, account, filestore=None, data=None):
        self.name=name
        self.account_num=account        
        self.filestore=filestore                        
        self.account_data = data if data else json.load(filestore)
        if filestore:
            filestore.seek(0)

    @staticmethod
    def FileName(filestore, account):
        return os.path.join(filestore.ACCOUNT_DIR,account)
    
    @classmethod
    def ExecuteAction(cls, name, account, filestore, action):
        args=[]
        success=-1
        if action in ['deposit', 'withdraw']:
            args.append(float(raw_input('Please enter amount:\n=> ')))
            with open(cls.FileName(filestore,account), 'r+') as outfilestore: 
                filestore.locker.lockf(outfilestore,LOCK_EX)               
                ba=BankAccount(name, account, outfilestore) 
                success=getattr(ba , action)(*args)                 
                filestore.locker.unlockf(outfilestore)
        elif action=='transfer':
            args.append(float(raw_input('Please enter amount:\n=> ')))
            args.append(raw_input('Please enter account to transfer to:\n=> '))
            with open(cls.FileName(filestore,account), 'r+') as a, open(cls.FileName(filestore,args[1]),'r+') as b:
                if int(account) <int(args[1]):
                    filestore.locker.lockf(a,LOCK_EX)
                    filestore.locker.lockf(b,LOCK_EX)
                else:
                    filestore.locker.lockf(b,LOCK_EX)
                    filestore.locker.lockf(a,LOCK_EX)        
                args.append(b)
                success = getattr(BankAccount(name, account, a) , action)(*args)                                   
                filestore.locker.unlockf(a)        
                filestore.locker.unlockf(b)        
        else:
            #logger.warn('unrecognized action %s' % (action))
            data = filestore.read(cls.FileName(filestore,account), uselock=True)
            ba=BankAccount(name, account, data=data) 
            success=getattr(ba, action)()
            
        if success >=0 :
            logger.warn('ACTION: %s succeeded, ACCOUNT:%s  BALANCE is %d' %(action.upper(), account, success))
        else:
            logger.error('Action: %s failed' % action)
        
    def deposit(self, amount):
        if amount>0:
            self.account_data['balance'] = amount+self.balance()
            if self.filestore:
                self.filestore.truncate()
                json.dump(self.account_data, self.filestore)
            return self.balance()
        return -1

    def withdraw(self, amount):
        if self.balance()>=amount and amount>0:
            self.account_data['balance'] = self.balance()-amount
            if self.filestore:
                self.filestore.truncate()
                json.dump(self.account_data, self.filestore)
            return self.balance()
        return -1

    def balance(self):
         return self.account_data.get('balance',0.0)

    #TODO: what if the withdraw succeeds and bank acount fails what about rollback
    def transfer(self, amount, account_to,filestore_to):
        if self.balance()>=amount and amount>0:
            self.withdraw(amount)
            BankAccount('to',account_to, filestore_to).deposit(amount)            
            return self.balance()
        return -1
        
    @staticmethod
    def GenerateAccountNumber(filestore):
        filename=FileStore.ACCOUNT_MAX
        with open(filename, 'r+') as outfile:
            filestore.locker.lockf(outfile,LOCK_EX)
            data = json.load(outfile)
            data['max_account']=data['max_account']+1   
            outfile.seek(0)                         
            json.dump(data, outfile)
            outfile.truncate()
            filestore.locker.unlockf(outfile)
        return data['max_account']
        
    @classmethod
    def WriteAccount(cls, account, filestore):
        outfile=cls.FileName(filestore,account)      
        data = {'account': account,'currency':'usd','balance':0}
        filestore.write(outfile, data)
        return True
        
    
#TODO: once user logs in we should note it and force logout when done
class User:
    def __init__(self, user, passwd, filestore, create=False):        
        self.user_data={}
        self.user=user
        self.userfile =os.path.join(FileStore.USER_DIR,self.user)
        if os.path.exists(self.userfile):
            if create:
                logger.warn(' user exists, please choose another user name')
                raise BaseException('user name exists')
            self.user_data=filestore.read(self.userfile, uselock=True)
        elif user=='admin':
            self.user_data= {'name':'admin','pin':'1234'}
        elif create:
            self.user_data={ 'name': user, 'pin': passwd, 'accounts' : [], 'is_locked' : False }
            self.open(filestore, create=True)
        else:
            logger.warn(self.userfile + ' does not exist')
            raise BaseException('user does not exist')        
        if not self.isPassword(passwd):
            raise  BaseException('password is incorrect')
        #if self.isUserLoggedIn(user):
        #   raise 'user already loggedin'        

    def isUserLoggedIn(self):
        return self.user_data.get('is_locked',False)==True

    def isPassword(self, passwd):
        logger.info('password is %s' % self.user_data.get('pin'))
        return self.user_data.get('pin')==passwd

    def accounts(self):
        return self.user_data.get('accounts')

    def name(self):
        return self.user_data.get('name')

    def executeAction(self, action, filestore):
        if action=='open':
            self.open(filestore)
        else:            
            accountenum = enum(*self.accounts())            
            choice = raw_input('Please select an account:\n' + '\n'.join([str(key)+': '+value for key,value in accountenum.reverse_mapping.items()])+'\n=> ')
            account = accountenum.reverse_mapping.get(int(choice))
            logger.warn('Account selected is '+ str(account))
            if account:
                BankAccount.ExecuteAction(self.name, account, filestore, action)

    def open(self, filestore, create=False):
        account = BankAccount.GenerateAccountNumber(filestore)
        account=str(account)
        if not create:
            logger.warn('Creating New account = %s for user: %s' % (account, self.user))
        self.writeuser(account,filestore, create)
        BankAccount.WriteAccount(account, filestore)

    def writeuser(self, account, filestore, create=False): 
        logger.warn('Creating user %s with account: %s' % (self.user, account))
        code='r+' if not create else 'w'
        with open(self.userfile, code) as filename:
            filestore.locker.lockf(filename,LOCK_EX)
            if not create:
                self.user_data = json.load(filename)
                filename.seek(0)
            self.accounts().append(account)
            json.dump(self.user_data, filename)
            filename.truncate()
            filestore.locker.unlockf(filename)
        return True
    
class AccountingSystem(object):
    ACTOR_TYPE = enum('ADMINISTRATOR', 'CUSTOMER', 'HELP','EXIT')
    CUST_ACTION_TYPE = enum('open','deposit','withdraw','transfer','balance')
    ADMIN_ACTION_TYPE = enum('restart', 'initialize', 'newuser', 'userlist')
    ADMIN_PASSWORD='admin' 

    def __init__(self):
        self.filestore=FileStore()
        self.User=None

    def restart(self):
        self.initialize(restart=True)
                     
    def initialize(self, restart=False):
        if not restart:
            logger.warn('Initializing system, remove all files')
            self.filestore.remove_all()   
            self.filestore.write(FileStore.ACCOUNT_MAX, {'max_account': 110000000})  
            logger.warn('Provide initial account data:')
            data = {'admin' : {  'name': '', 'pin': '1234', },
                    'piggy1' : { 'name':'pig1', 'pin': '1234', 'accounts' : ['110000000'], 'is_locked' : False },
                    'piggy2' : { 'name':'pig2', 'pin': '1234', 'accounts' : ['110000001'], 'is_locked' : False },
                   }
            logger.warn('Base user and account data:\n %s' % (str(data)))
            for user, value in data.items():
                self.filestore.write(os.path.join(FileStore.USER_DIR,user), value)
                accounts = value.get('accounts',[])
                for account in accounts:
                    self.filestore.write(os.path.join(FileStore.ACCOUNT_DIR,account), {'account' : account, 'currency':'usd','balance':0})
        else:
            #TODO: cleanup such as remove locks if invalid state
            pass
    
    def newuser(self):
        name = raw_input('Please enter a new user name => ')
        pin = raw_input('Please enter a new pin => ')
        User(name, pin,self.filestore, create=True) 
    
    def userlist(self):  
        users = [f for f in os.listdir(FileStore.USER_DIR) if os.path.isfile(os.path.join(FileStore.USER_DIR, f))]
        print users
        
    def prompt_values(self, prompt_type):
        return '\n'.join([str(key)+':'+value for key,value in prompt_type.reverse_mapping.items()])+'\n'
        
    def welcome(self):
        msg='This is the Piggy Bank Accounting System Program.\nAdministrator can reset system via initialize action.\n'
        msg+='Customer actions: deposit, withdrawl, transfer, create new account.\n\n'
        msg+='Please choose who you are:\n'
        admin_or_cust = raw_input(msg+self.prompt_values(self.ACTOR_TYPE)+'=> ')
        return admin_or_cust
    
    def admin_options(self):
        passwd=None
        logger.warn('Force admin passwd re-entry for each action.')
        #if not self.User:
        passwd = raw_input('Please enter the admin password:\n=> ')
        self.User = User('admin', passwd,self.filestore)
        return raw_input('Select an action:\n'+self.prompt_values(self.ADMIN_ACTION_TYPE).upper()+'=> ')        
    
    def cust_options(self):
        action=raw_input('Please select a customer action:\n'+self.prompt_values(self.CUST_ACTION_TYPE).upper()+'=> ')
        return action
    
    def prompt(self):
        actor = self.welcome()
        not_finished='Y'
        while(not_finished=='Y'):
            try:
                if int(actor) == self.ACTOR_TYPE.CUSTOMER:
                    if not self.User:
                        name=raw_input('Please enter user name:\n=> ')
                        if name.lower()=='admin' or name.lower()=='':
                            raise BaseException('User: \"%s\" cannot be a customer'% (name))
                        passwd=raw_input('Please enter the access code:\n=> ') 
                        self.User = User(name, passwd,self.filestore) 
                    action=self.cust_options()      
                    self.User.executeAction(self.CUST_ACTION_TYPE.reverse_mapping.get(int(action)), self.filestore)
                    not_finished = raw_input('Do you need to do another transaction? Y or N\n=> ')
                elif int(actor) == self.ACTOR_TYPE.ADMINISTRATOR:
                    logger.warn('User is admin:')
                    action=self.admin_options()
                    getattr(self, self.ADMIN_ACTION_TYPE.reverse_mapping[int(action)], lambda : None)()
                    not_finished = raw_input('Do you need to do another transaction? Y or N\n=> ')
                elif int(actor) == self.ACTOR_TYPE.HELP:
                    actor = self.welcome()
                elif int(actor) == self.ACTOR_TYPE.EXIT:
                    print 'Exiting...'
                    return
                else:
                    print 'invalid user type selection!'
                    actor = self.welcome()
            except BaseException as err:
                logger.error(str(err))
                self.passwd=''
                not_finished = raw_input('Do you need to do another transaction? Y or N\n=> ')        
        print 'Exiting...'
        
def test_all_interactive():
    BankAccount.ExecuteAction('piggy2', '110000001', FileStore(), 'balance')
    BankAccount.ExecuteAction('piggy2', '110000001', FileStore(), 'deposit')
    BankAccount.ExecuteAction('piggy2', '110000001', FileStore(), 'withdraw')

def test_noninteractive():
    #test balance, deposit, withdraw
    pass

#TODO: list account data from admin for a user
if __name__=='__main__':
    #print TEMPDIR
    AccountingSystem().prompt()
    
