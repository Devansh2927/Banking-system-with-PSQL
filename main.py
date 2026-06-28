from database import connect_to_database
import hashlib
import random ,string
import os
import psycopg2

#=====================================ENCRYPT AND VERIFY PIN====================
def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_pin(pin, stored_pin_hash):
    return hash_pin(pin)==stored_pin_hash


#===============================db and table initialize=================
def inialize_tables():
    connection =connect_to_database()
    if not connection:
        return False

    try:
        cursor =connection.cursor()

        create_accounts_table ="""
        CREATE TABLE IF NOT EXISTS accounts (
           account_number VARCHAR(50) PRIMARY KEY,
           name VARCHAR(100) NOT NULL,
           pin VARCHAR(64) NOT NULL,
           balance DECIMAL(15,2) DEFAULT 0.00,
           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        create_audit_table ="""
        CREATE TABLE IF NOT EXISTS audit (
            id SERIAL Primary Key,
            account_number VARCHAR(50),
            holder_name VARCHAR(100) NOT NULL,
            action VARCHAR(64) NOT NULL,
            amount  DECIMAL(15,2) DEFAULT 0.00,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(account_number) REFERENCES accounts(account_number) ON DELETE SET NULL
        );
    """

        # Agar table pehle se exist karti hai purane (ON DELETE rule ke bina)
        # foreign key constraint ke saath, to use yahan patch/fix kar do
        fix_existing_constraint = """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'audit_account_number_fkey'
                AND table_name = 'audit'
            ) THEN
                ALTER TABLE audit DROP CONSTRAINT audit_account_number_fkey;
                ALTER TABLE audit
                    ADD CONSTRAINT audit_account_number_fkey
                    FOREIGN KEY (account_number)
                    REFERENCES accounts(account_number)
                    ON DELETE SET NULL;
            END IF;
        END $$;
        """


        cursor.execute(create_accounts_table)
        cursor.execute(create_audit_table)
        cursor.execute(fix_existing_constraint)

        connection.commit()
        cursor.close()
        return True
    except Exception as error:
        print(f"Error initializing tables :{error}")
        return False

#==================================Account class
class Account:
    def __init__(self, name="",pin ="", account_number=""):
        self.__account_number = (
            account_number if account_number else self.__generate_account_number()
        ) 
        self.__name=name
        self.__pin=hash_pin(pin)
        self.__plain_pin=pin
        self.__balance =0.0

    @staticmethod
    def __generate_account_number():
        return "".join(random.choices(string.ascii_uppercase + string.digits,  k=10))

#===================================getters
    def get_account_number(self):
        return self.__account_number

    def get_name(self):
        return self.__name

    def get_pin_hash(self):
        return self.__pin

    def get_plain_pin(self):
        return self.__plain_pin

    def get_balance(self):
        return self.__balance

#=================================setters===============================
    def set_name(self,name):
        self.__name = name

    def set_pin(self, pin):
        self.__pin = hash_pin(pin)
        self.__plain_pin = pin

    def set_pin_hash(self,pin):
        self.__pin = hash_pin(pin)

    def set_balance(self,balance):
        self.__balance = balance


#===========================Utility==============================================
    def deposit(self,amount):
        if amount <=0:
            return False
        self.__balance +=amount
        return True

    def withdraw(self,amount) -> bool:
       if amount <=0 or amount >self.__balance:
        return False
       self.__balance -= amount
       return True

#===========================Database CRUD=========================================
    @classmethod
    def load_from_db(cls, account_number,pin):

        connection =connect_to_database()
        if not connection:
            return False
        try:
            cursor =connection.cursor()
            cursor.execute(
            "SELECT account_number,name,pin,balance FROM accounts WHERE account_number=%s",
            (account_number,),
            )
            result =cursor.fetchone()
            connection.commit()
            cursor.close()
            if result:
                stored_pin_hash = result[2]
                if  verify_pin(pin,stored_pin_hash):
                    account =cls(result[1],pin,result[0])
                    # account._Account_pin =stored_pin_hash
                    #restore the balance
                    account.set_balance(float(result[3]))
                    return account
            return None
        except Exception as error:
            print (f"Error loading account, {error}")
            return None

    def save_to_db(self):
        connection = connect_to_database()
        if not connection:
            return False

        try:
            cursor = connection.cursor()
            cursor.execute(
            """
            INSERT INTO accounts(account_number, name, pin, balance)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (account_number)
            DO UPDATE SET
                name = %s,
                pin = %s,
                balance = %s
            """,
            (
                self.__account_number,
                self.__name,
                self.__pin,
                self.__balance,
                self.__name,
                self.__pin,
                self.__balance,
               )
        )
            connection.commit()
            cursor.close()
            return True

        except Exception as error:
            print(f"Error creating/updating account: {error}")
            return False

    def delete_from_db(self):
        connection =connect_to_database()

        if not connection:
            return False
        try:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM accounts WHERE account_number = %s",
                (self.__account_number,)
            )

            connection.commit()
            cursor.close()
            return True

        except Exception as error:
            print(f"Error deleting account: {error}")
            return False

#==========================Audit class
class Audit:
    @staticmethod
    def log_action(account_number,holder_name,action,amount=0.0):
        connection =connect_to_database()
        if not connection:
            return False
        try:
            cursor=connection.cursor()
            cursor.execute(
               "Insert INTO audit (account_number,holder_name,action,amount)VALUES(%s,%s,%s,%s)",
               (
                    account_number,
                    holder_name,
                    action,
                    amount,
                ),
            )
            connection.commit()
            cursor.close()
            return True
        except Exception as error:
            print(f"Error auditing action,{error}")
            return None


    @staticmethod
    def get_single_audit_logs(account_number):
        connection =connect_to_database()
        if not connection:
            return False
        try:
            cursor =connection.cursor()
            cursor.execute(
                """
                SELECT id, holder_name,action,amount,timestamp
                FROM audit
                WHERE account_number =%s
                ORDER BY timestamp DESC
            """,
                (account_number,),

            )
            results =cursor.fetchall()
            connection.commit()
            cursor.close()
            logs= []
            for row in results:
                logs.append(
                    {
                        "id":row[0],
                        "holder_name": row[1],
                        "action":row[2],
                        "amount": row[3],
                        "timestamp":row[4],
                    }

                )
            return logs
        except Exception as error:
           print(F"Error logging {account_number} action,{error}")
           return None

    @staticmethod
    def get_all_audit_logs():
        connection =connect_to_database()
        if not connection:
            return False
        try:
            cursor =connection.cursor()
            cursor.execute(
                """
                SELECT id, account_number,holder_name,action,amount,timestamp
                FROM audit
                ORDER BY timestamp DESC
            """
            )
            results =cursor.fetchall()
            connection.commit()
            cursor.close()
            logs= []
            for row in results:
                logs.append(
                    {
                        "id":row[0],
                        "account_number": row[1],
                        "holder_name":row[2],
                        "action":row[3],
                        "amount": row[4],
                        "timestamp":row[5],
                    }

                )
            return logs
        except Exception as error:
           print(F"Error logging  action,{error}")
           return False


    @staticmethod
    def clear_all_audit_logs():
        connection = connect_to_database()
        if not connection:
            return  False

        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM audit")
            connection.commit()
            cursor.close()
            return True
        except Exception as error:
            print(f"Error clearing all audit logs: {error}")
            return False



#==========================Bank system class==============================
class BankSystem:

    def __init__(self):
        inialize_tables()

    def create_account(self, name, pin):
        account =Account(name, pin)
        if account.save_to_db():
            Audit.log_action(
                account.get_account_number(),account.get_name(),"Account Created",0.0
            )
            return account
        return None
    def read_account(self,account_number,pin):
        account =Account.load_from_db(account_number,pin)
        if account:
            Audit.log_action(account_number,account.get_name(),"Detailed Checked",0.0)
            return account
        return None

    def update_account(self,account):
        return account.save_to_db()

    def delete_account(self,account_number,pin):
        account =Account.load_from_db(account_number,pin)
        if account:
            # Pehle audit log karo, account delete hone se pehle
            # (account delete hone ke baad iska account_number FK satisfy nahi hoga)
            Audit.log_action(
                account_number,account.get_name()," Account Deleted",0.0
            )
            success=account.delete_from_db()
            if success:
                return True
        return False

    def deposit(self,account_number,pin,amount):
        account =Account.load_from_db(account_number,pin)
        if account and account.deposit(amount):
            account.save_to_db()
            Audit.log_action(
                account_number,account.get_name(),"Amount Deposited",amount
            )
            return True
        return False


    def withdraw(self,account_number,pin,amount):
        account =Account.load_from_db(account_number,pin)
        if account and account.withdraw(amount):
            account.save_to_db()
            Audit.log_action(
                account_number,account.get_name(),"Amount withdrawn",amount
            )
            return True
        return False

    def get_account_balance(self,account_number,pin):
        account =Account.load_from_db(account_number,pin)
        if account:
            Audit.log_action(account_number,account.get_name(),"Balance checked",0.0)
            return account.get_balance()
        return None

    def get_single_audit_logs(self,account_number):
       return Audit.get_single_audit_logs(account_number)

    def get_all_audit_logs(self):
       return Audit.get_all_audit_logs()

    def clear_audit_logs(self):
        return Audit.clear_all_audit_logs()

#=====================Utility functions=======================

def get_valid_amount(prompt):
    while True:
        try:
            amount = float(input(prompt))
            if amount <= 0:
                print("Amount must be greater than zero.")
                continue
            return amount
        except ValueError:
            print("Please enter a valid number.")


#============== CLI Main menu  functions=======================
def create_account_cli(bank):
    """
    Account creation handle karta hai
    
    Arguments:
    - bank (BankSystem): BankSystem object operations ke liye
    
    Kya karta hai:
    1. User se account details collect karta hai
    2. Validation karta hai input ki
    3. Naya account create karta hai
    4. Success/error messages dikhata hai
    
    Kaise help karta hai:
    - User onboarding ko facilitate karta hai
    - Data collection karta hai
    - Feedback provide karta hai
    """
    print("=" * 40)
    print("  CREATE NEW ACCOUNT")
    print("=" * 40)
    
    name = input("Enter your Name: ").strip()
    if not name:
        print("Don't leave name empty.")
        input("Press Enter to continue...")
        return

    # PIN le leta hai bina masking ke
    pin = input("4-digit PIN daalo: ").strip()
    if len(pin) != 4 or not pin.isdigit():
        print("PIN must be 4-digit number.")
        input("Press Enter to continue...")
        return

    confirm_pin = input("Confirm PIN No: ").strip()
    if pin != confirm_pin:
        print("PIN  doesnot match.")
        input("Press Enter to continue...")
        return

    account = bank.create_account(name, pin)
    if account:
        print(f"\nAccount successfully Created!")
        print(f"Account Number: {account.get_account_number()}")
        print("Enter &Save your account number and PIN safely.")
    else:
        print("\n Error Occured while creating your acount, Try again Please !")

    input("Press Enter to continue...")

def login_to_account_cli(bank):
    print("=" * 40)
    print("      ACCOUNT LOGIN")
    print("=" * 40)

    account_number = input("Enter account number: ").strip()
    if not account_number:
        print("Account number cannot be left empty.")
        input("Press Enter to continue...")
        return

    pin = input("Enter PIN No: ").strip()

    account = bank.read_account(account_number, pin)
    if not account:
        print("Wrong account number or PIN.")
        input("Press Enter to continue...")
        return

#===========Account operations Menu====================

    while True:
        print("=" * 40)
        print(f" WELCOME, {account.get_name()}!")
        print(f" ACCOUNT: {account.get_account_number()}")
        print("=" * 40)
        print("1. Check Balance")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Check Transaction History ")
        print("5. Update Account Info ")
        print("6. Delete Account ")
        print("7. Logout")
        print("=" * 40)
        
        choice = input("Enter your choice (1-7): ").strip()
        
        if  choice == '1':
            check_balance_cli(bank, account)
        elif choice =='2':
            deposit_money_cli(bank, account)
        elif choice == '3':
            withdraw_money_cli(bank, account)
        elif choice == '4':
            view_transaction_history_cli(bank, account)
        elif choice == '5':
            update_account_info_cli(bank, account)
        elif choice == '6':
            if delete_account_cli(bank, account):
                break  # Deletion ke baad main menu par wapas jaao
        elif choice == '7':
            break  # Logout
        else:
            print("Invalid choice,try again.")
            input("Press Enter to continue...")

def check_balance_cli(bank, account):
    """
    Account balance check karta hai
    
    Arguments:
    - bank (BankSystem): BankSystem object operations ke liye
    - account (Account): Current logged-in account
    
    Kya karta hai:
    1. Account balance fetch karta hai
    2. Balance display karta hai user ko
    3. User input wait karta hai continue karne ke liye
    
    Kaise help karta hai:
    - Financial awareness promote karta hai
    - Account information provide karta hai
    - User inquiry satisfy karta hai
    """
    print("=" * 40)
    print("    ACCOUNT BALANCE")
    print("=" * 40)
    
    balance = bank.get_account_balance(account.get_account_number(), account.get_plain_pin())
    if balance is not None:
        print(f"Current Balance: ${balance:.2f}")
    else:
        print("Balance cannot be generated.")
    
    input("Press Enter to continue...")

def deposit_money_cli(bank, account):
    print("=" * 40)
    print("     Deposit your Money ")
    print("=" * 40)

    amount = get_valid_amount("Enter the amount to deposit: $")
    plain_pin = account.get_plain_pin()

    if bank.deposit(account.get_account_number(),
                    plain_pin, amount):
        print(f"${amount:.2f} successfully deposited!")
        # Display ke liye account balance update karo
        account = bank.read_account(account.get_account_number(), plain_pin)
        if account:
            print(f"New Balance: ${account.get_balance():.2f}")
    else:
        print("Error Occured!, try again please.")
    
    input("Press Enter to continue...")


def withdraw_money_cli(bank, account):
    """
    Paise nikalne ka kaam handle karta hai
    Arguments:
    - bank (BankSystem): BankSystem object operations ke liye
    - account (Account): Current logged-in account
    
    Kya karta hai:
    1. User se amount collect karta hai
    2. Withdrawal operation perform karta hai
    3. Success/error messages dikhata hai
    4. Updated balance display karta hai
    
    Kaise help karta hai:
    - Funds withdrawal process ko manage karta hai
    - Transaction feedback provide karta hai
    - User experience enhance karta hai
    """
    print("=" * 40)
    print("        Withdraw Money")
    print("=" * 40)

    amount = get_valid_amount("Enter the amount to  withdraw: $")
    plain_pin = account.get_plain_pin()

    if bank.withdraw(account.get_account_number(), plain_pin, amount):
        print(f"${amount:.2f}  Transcation successfully Completed!")
        # Display ke liye account balance update karo
        account = bank.read_account(account.get_account_number(), plain_pin)
        if account:
            print(f"New Balance: ${account.get_balance():.2f}")
    else:
        print("Insufficient money or wrong amount entered.")

    input("Press Enter to continue...")

def view_transaction_history_cli(bank, account):

    print("=" * 40)
    print("      TRANSACTION HISTORY")
    print("=" * 40)

    logs = bank.get_single_audit_logs(account.get_account_number())
    if not logs:
        print("No transaction history found.")
    else:
        print(f"{'ID':<5} {'Naam':<15} {'Action':<20} {'Amount':<10} {'Time':<20}")
        print("-" * 70)
        for log in logs:
            amount_str = f"${log['amount']:.2f}" if log['amount'] > 0 else ""
            print(f"{log['id']:<5} {log['holder_name']:<15} {log['action']:<20} {amount_str:<10} {log['timestamp']:<20}")

    input("Press Enter to continue...")

def update_account_info_cli(bank, account):

    print("=" * 40)
    print("      UPDATE ACCOUNT INFO  ")
    print("=" * 40)
    print("1. Change name ")
    print("2. Change PIN ")
    print("3. Go back to account menu")
    print("=" * 40)


    choice = input("Enter your choice (1-3): ").strip()

    if choice == '1':
        new_name = input(" Enter New  name: ").strip()
        if new_name:
            account.set_name(new_name)
            if bank.update_account(account):
                print("Name successfully updated !")
            else:
                print("Some error in updating Name.")
        else:
            print("Don't leave name empty.")
    elif choice == '2':
        old_pin = input(" Enter Current PIN : ").strip()
        if  verify_pin(old_pin, account.get_pin_hash()):
            new_pin = input("Enter new 4-digit PIN: ").strip()
            if len(new_pin) == 4 and new_pin.isdigit():
                confirm_pin = input("Enter new PIN number: ").strip()
                if new_pin == confirm_pin:
                    account.set_pin(new_pin)
                    if bank.update_account(account):
                        print("PIN successfully updated!")
                    else:
                        print("Problem in updating PIN .")
                else:
                    print("PIN doesnot match.")
            else:
                print("PIN must be 4-digit.")
        else:
            print("Wrong current PIN.")
    elif choice != '3':
        print("Wrong  choice.")
    
    input("Press Enter to continue...")

def delete_account_cli(bank, account):

    print("=" * 40)
    print("       ACCOUNT DELETE ")
    print("=" * 40)
    print("WARNING: Action  cannot be reversed again !")
    print("Confirmation your choice:")
    print(f"1. Account Number: {account.get_account_number()}")
    print("2. Apka PIN")
    print("=" * 40)


    confirmation = input(" Are you sure you want to  delete your account? (yes/no): ").strip().lower()
    if confirmation != 'yes':
        print("Account deletion canceled.")
        input("Press Enter to continue...")
        return False

    # Security ke liye account number aur PIN verify karo
    acc_num_input = input("Enter your account number again: ").strip()
    pin_input = input("Enter  your PIN : ").strip()

    if  acc_num_input == account.get_account_number() and verify_pin(pin_input, account.get_pin_hash()):
        if bank.delete_account(account.get_account_number(), pin_input):
            print("Account successfully deleted!")
            input("Press Enter to continue...")
            return True
        else:
            print("Error occured during deleting your account.")
    else:
        print("Wrong pin or account number. Deletion canceled .")
    
    input("Press Enter to continue...")
    return False


def admin_view_audit_logs_cli(bank):
    """
    Admin function sab audit logs dekhne ke liye

    Arguments:
    - bank (BankSystem): BankSystem object operations ke liye

    Kya karta hai:
    1. Sab accounts ki audit logs fetch karta hai
    2. Admin ko complete transaction overview deta hai
    3. Formatted display karta hai logs ka

    Kaise help karta hai:
    - System monitoring ke liye use hota hai
    - Administrative oversight provide karta hai
    - Compliance reporting karta hai
    """
    print("=" * 40)
    print("       All AUDIT LOGS")
    print("=" * 40)

    # Security ke liye real system mein iski protection password se ki ja sakti hai
    logs = bank.get_all_audit_logs()
    if not logs:
        print("No  audit logs found.")
    else:
        print(f"{'ID':<5} {'Account':<12} {'Naam':<15} {'Action':<20} {'Amount':<10} {'Time':<20}")
        print("-" * 85)
        for log in logs:
            amount_str = f"${log['amount']:.2f}" if log['amount'] > 0 else ""
            account_num_str = log['account_number'] if log['account_number'] else "[deleted]"
            print(f"{log['id']:<5} {account_num_str:<12} {log['holder_name']:<15} {log['action']:<20} {amount_str:<10} {log['timestamp']:<20}")

    input("Press Enter to continue...")

def admin_clear_audit_logs_cli(bank):
    """
    Admin function sab audit logs clear karne ke liye
    
    Arguments:
    - bank (BankSystem): BankSystem object operations ke liye
    
    Kya karta hai:
    1. Admin se confirmation maangta hai
    2. Sab audit logs clear karta hai
    3. Success/error messages dikhata hai
    
    Kaise help karta hai:
    - Database maintenance ke liye use hota hai
    - Storage optimization karta hai
    - Privacy compliance maintain karta hai
    """
    print("=" * 40)
    print("      CLEAR  AUDIT LOGS")
    print("=" * 40)
    print("WARNING: This will delete audit logs  permanently!")
    print("=" * 40)
    
    confirmation = input("Are you sure you want to clear all audit logs ? (yes/no): ").strip().lower()
    if confirmation == 'yes':
        if bank.clear_audit_logs():
            print("All audit logs successfully cleared!")
        else:
            print(" Problem in clearing Audit logs .")
    else:
        print("transcation canceled.")
    
    input("Press Enter to continue...")

def main_menu_cli():
    """
    Main menu display karta hai aur user choices handle karta hai
    
    Arguments:
    - Koi argument nahi leta
    
    Kya karta hai:
    1. Main menu display karta hai
    2. User input collect karta hai
    3. Selected operation execute karta hai
    4. Program flow manage karta hai
    
    Kaise help karta hai:
    - User navigation ko facilitate karta hai
    - System access provide karta hai
    - Application control manage karta hai
    """
    bank = BankSystem()

    while True:
        print("=" * 40)
        print("BANK MANAGEMENT SYSTEM")
        print("=" * 40)
        print("1. Create new Account ")
        print("2. Login Account")
        print("3. Admin - See   Audit Logs")
        print("4. Admin - Clear Audit Logs")
        print("5. Exit")
        print("=" * 40)

        choice = input("Enter your choice (1-5): ").strip()

        if choice == '1':
            create_account_cli(bank)
        elif choice == '2':
            login_to_account_cli(bank)
        elif choice == '3':
            admin_view_audit_logs_cli(bank)
        elif choice == '4':
            admin_clear_audit_logs_cli(bank)
        elif choice == '5':
            print("Thank you for Using our Bank Management System !")
            break
        else:
            print("Wrong choice. Try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main_menu_cli()


















