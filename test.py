"""this is the testing file"""
from os import system

def main():
    """this is the main function"""
    system('start "A" python DVR.py A 5000 configA.txt')
    system('start "B" python DVR.py B 5001 configB.txt')
    system('start "C" python DVR.py C 5002 configC.txt')
    system('start "D" python DVR.py D 5003 configD.txt')
    system('start "E" python DVR.py E 5004 configE.txt')
    system('start "F" python DVR.py F 5005 configF.txt')


if __name__ == "__main__":
    main()


