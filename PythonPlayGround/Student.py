from sympy import true


class Student:
    def __init__(self, name, age, is_male):
        self.name=name
        self.age=age
        self.is_male=is_male

    def is_male_gender(self):
        if(self.is_male == True) :
            return True
        else:
            return False