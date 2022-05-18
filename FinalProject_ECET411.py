from tkinter import *
from tkinter.messagebox import showinfo
from os.path import exists
from time import sleep
from gpiozero import LED, Servo
import json
import digitalio
import board
import adafruit_matrixkeypad
from cryptography.fernet import Fernet

# setup encryption
key = b'pdv4ABwAgu-dXsZf1kBfaKg28DUVllf50VrrMm38tiQ='
f = Fernet(key)


def encrypt(decrypted_passcode):
    fernet_token = f.encrypt(decrypted_passcode.encode("utf-8"))
    return fernet_token


def decrypt(fernet_token):
    decrypted_passcode = f.decrypt(fernet_token).decode("utf-8")
    return decrypted_passcode


# setup outputs
servo = Servo(4)
red = LED(17)
green = LED(27)
blue = LED(22)

# setup keypad
cols = [digitalio.DigitalInOut(x) for x in (
    board.D10, board.D9, board.D11, board.D5)]
rows = [digitalio.DigitalInOut(x) for x in (
    board.D6, board.D13, board.D19, board.D26)]

keys = (("1", "2", "3", "A"),
        ("4", "5", "6", "B"),
        ("7", "8", "9", "C"),
        ("*", "0", "#", "D"))

keypad = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keys)


# Initializing Locker
settings_file_name = "FootLocker.json"
rt_vars = dict()
if exists(settings_file_name):
    # Load configuration information if it exists
    file = open(settings_file_name, 'r')
    rt_vars_text = file.read()
    rt_vars = json.loads(rt_vars_text)
    decrypted_code = decrypt(rt_vars["user_code"].encode("utf-8"))
    user_code = decrypted_code
else:
    # Initialize Default Values
    default_pass = encrypt("0000")
    rt_vars["user_code"] = default_pass.decode("utf-8")
    # save Default Values
    rt_vars_json = json.dumps(rt_vars)
    file = open(settings_file_name, "w")
    file.write(rt_vars_json)
    file.close()
    user_code = decrypt(rt_vars["user_code"].encode("utf-8"))

servo.min()


def changer():
    '''Initialize Pop-Up GUI to change passcode'''
    global pop
    blue.on()
    new_code = StringVar()
    pop = Toplevel(root)
    pop.title("Change Passcode")
    pop.geometry("250x150")
    pop_label = Label(pop, text="Enter new Passcode..")
    pop_label.pack(pady=10)
    new_code_entry = Entry(pop, textvariable=new_code)
    new_code_entry.pack(pady=5)
    pop_frame = Frame(pop)
    pop_frame.pack(pady=5)
    accept = Button(pop_frame, text="Accept",
                    command=lambda: save(new_code.get()))
    accept.grid(row=0, column=1)
    cancel = Button(pop_frame, text="Cancel", command=lambda: pop.destroy())
    cancel.grid(row=0, column=2)


def save(new_code):
    '''save new passcode'''
    pop.destroy()
    global rt_vars
    global user_code
    blue.off()
    green.blink(on_time=0.25, off_time=0.25, n=3)
    encrypted_passcode = encrypt(new_code)

    rt_vars["user_code"] = encrypted_passcode.decode("utf-8")
    user_code = decrypt(rt_vars["user_code"].encode("utf-8"))
    print(
        f'Encrypted code: {rt_vars["user_code"]}\nDecrypted code: {user_code}')
    file = open(settings_file_name, "w")
    rt_vars_json = json.dumps(rt_vars)
    file.write(rt_vars_json)
    file.close()


def error():
    '''blink red LED 3 times when wrong passcode entered'''
    green.off()
    blue.off()
    red.blink(on_time=0.25, off_time=0.25, n=3)


def clear_code():
    code_entry.delete(0, 'end')


def check_code():
    '''action performed when unlock btn pressed'''
    count = 0
    blue.on()
    while True:
        keys = keypad.pressed_keys
        if keys:
            code_entry.insert(count, keys)
            count += 1
        if count >= 4:
            break
        sleep(0.200)
    if passcode.get() == user_code:
        blue.off()
        green.on()
        servo.max()
        showinfo(title='unlock message', message='unlock succesful')
        sleep(1)
        green.blink(on_time=0.25, off_time=0.25)
        clear_code()
    else:
        error()
        servo.min()
        showinfo(title='unlock message', message='unlock unsuccesful')
        clear_code()


def lock():
    servo.min()
    green.off()


# Initialize Main GUI
root = Tk()

root.geometry('425x300')
root.title("Lock Security System (Encrypted)")

label1 = Label(root, text='Press the buttons to perform desired actions')
label1.pack()

passcode = StringVar()
code_entry = Entry(root, textvariable=passcode)
code_entry.pack(pady=5)

unlock_btn = Button(root, text='Unlock',
                    command=lambda: check_code())
unlock_btn.pack()

lock_btn = Button(root, text='Lock',
                  command=lambda: lock())
lock_btn.pack()

change_btn = Button(root, text='Change Pin',
                    command=lambda: changer())
change_btn.pack()

save_btn = Button(root, text='Exit',
                  command=lambda: root.destroy())
save_btn.pack()


root.mainloop()
