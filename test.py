"""this is the testing file"""
from os import system

def main():
    """this is the main function"""
    system('start "A" python DVR.py A 5000 newA.txt')
    system('start "B" python DVR.py B 5001 newB.txt')
    system('start "C" python DVR.py C 5002 newC.txt')
    system('start "D" python DVR.py D 5003 newD.txt')


if __name__ == "__main__":
    main()


