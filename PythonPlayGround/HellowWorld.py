from math import *
from langchain_openai import ChatOpenAI
import HighSchoolStudent
import mymodule  # my module
from Student import Student
from HighSchoolStudent import HighSchoolStudent

def say_hi(name):
    print("Hello " + name)

def try_block(numerator, denominator):
    try:
        # 1. The 'risky' code goes here
        result = numerator / denominator 
    except ZeroDivisionError as e:
        # 2. Runs if a specific exception (dividing by zero) occurs
        print(f"Error: Cannot divide by zero. ({e})")
        return None
    except ValueError:
        # Can be used to catch other exceptions
        print("Error: Input value problem.")
        return None
    except Exception as e:
        # This catches almost all standard errors.
        print(f"An unexpected error occurred: {e}")
        return None
    else:
        # 3. Runs ONLY if the try block SUCCEEDED
        print("Division successful.")
        return result
    finally:
        # 4. ALWAYS runs, used for cleanup or guaranteed actions
        print("--- Finally Code ---")


name="Shiva"
age=2
male=True
print("Hellow World " + name.upper() + " age " + str(age) + " male: " + str(male))

ageInp = 12 #input("Enter age:")
ageInp = float(ageInp)
print(floor(ageInp))

# Lists
friends = ["Kevi", 2, True]
print (str(friends) + " - " + friends[0] + " - " + str(friends[1:3]))

# Tuples
coords = (4, 5)  # Is same as List but cannot change after creating
 
say_hi(name)

# Dict is same as JSON array
dict = { "1" : "Jan", 
         "2" : "Feb"
        }

print(dict["1"] + " " + dict.get("2") + " - " +   str(dict.keys()))
print(dict.keys())

try_block(10, 0)

try_block(10, "a")

try_block(10, 1)

# File
emp_file = open("employees.txt", "r+")  # r - read; w - write and override; a - Append; r+ - Read Write

print(emp_file.readable())

# emp_file.write("Sushma - Manager\n")
# arr = emp_file.readlines();
# print(arr);

emp_file_copy = open("employeeCopy.txt", "a") 


print("Print in for loop");
for emp in emp_file.readlines() :
    print(emp)
    emp_file_copy.write(emp)

emp_file.close();

#Module
mymodule.say_hello();

# Classes and Object
std1 = Student("Shiva", 51, True);
print(std1.name + " " + str(std1.is_male_gender()))

hsstd1 = HighSchoolStudent("Shiva", 51, True);
hsstd1.printHighSchool()
# Upcasting child → parent is automatic.: 
#           animal: Animal = Dog()
# Downcasting: animal = Dog()

class Person:
    def __init__(self, name):
        self.name = name

class Employee(Person):
    def __init__(self, name, emp_id):
        super().__init__(name)   # call parent constructor
        self.emp_id = emp_id