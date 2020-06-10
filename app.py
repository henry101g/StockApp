import os, csv, sys, sqlite3
import os.path
from flask import Flask, render_template, request, redirect
import sqlite3
from sqlite3 import Error
import re
#import yfinance as yf
#from yahoo_finance import Share
from yahoo_fin import stock_info as si

app=Flask(__name__)

students = []

init_balance="10000.00"

import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler


def getStockPrice():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))
    conn = sqlite3.connect(r"C:\xampp\htdocs\phpLiteAdmin\stock_market")
    cursor = conn.cursor()
    query=("select stock_code from stocks order by 1")
    cursor.execute(query)
    for row in (cursor.fetchall()):
        stock_code=row[0]        
        unit_price = si.get_live_price(stock_code)
        
        print("Stock code is: ",stock_code, "price is: ",unit_price)
        query=("update stocks set share_price = " + str(unit_price) + " where stock_code = '" + stock_code + "';")
        cursor.execute(query)
    
    conn.commit()
    conn.close()
    

scheduler = BackgroundScheduler()
scheduler.add_job(func=getStockPrice, trigger="interval", minutes=1)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())






@app.route("/")
def index():    
    return render_template("welcome.html")

@app.route("/login",methods=['GET', 'POST'])
def login():    
    return render_template("login-page.html")

@app.route("/validate-login",methods=['GET', 'POST'])
def check_login(username=False):
    conn = sqlite3.connect(r"C:\xampp\htdocs\phpLiteAdmin\stock_market")
    cursor = conn.cursor()
    auth=False # Assuming auth is false, need to authenticate user

    if not username: # The flow is the Login page flow
        auth=True # Need to authenticate user
        username=request.form.get("username")
        password=request.form.get("password")
    
        st=("select fname from users where username = '" + username + "' and password ='" + password + "';")
    else:
        st=("select fname from users where username = '" + username + "';")
    cursor.execute(st)
    row = (cursor.fetchone()) # Convert to str, trim by starting from the 2nd character, skip last two, convert to int

    if row is None:
        conn.close()
        return render_template("failure.html")
    
    name=row[0]
    

    owned_stocks = {}
    available_stocks = {}
    query=("""select purchased_stocks.stock_id, stock_name, stock_code, num_of_shares 
        from stocks, users, purchased_stocks
        WHERE
            users.user_id=(select user_id from users where username='""" + username + """') 
            and users.user_id=purchased_stocks.user_id
            and stocks.stock_id = purchased_stocks.stock_id""")
    cursor.execute(query)

    worth_of_stocks = 0

    for row in cursor.fetchall():
        stock={}
        stock_id=row[0]
        stock['stock_name']=row[1]
        stock['stock_code']=row[2]
        stock['num_of_shares']=row[3]
        st=("select share_price from stocks where stock_id =" + str(stock_id) + ";")
        cursor.execute(st)
        row = (cursor.fetchone())
        stock['unit_price'] = row[0]
        #stock['unit_price']=1
        stock['worth'] = stock['unit_price'] * stock['num_of_shares']
        worth_of_stocks = worth_of_stocks + stock['worth']
        
        owned_stocks[stock_id] = stock

        
    query=("select stock_id, stock_name, stock_code from stocks order by 1;")
            
    cursor.execute(query)

    for row in cursor.fetchall():
        stock={}
        stock_id=row[0]
        stock['stock_name']=row[1]
        stock['stock_code']=row[2]            
        st=("select share_price from stocks where stock_id =" + str(stock_id) + ";")
        cursor.execute(st)
        row = (cursor.fetchone())
        stock['unit_price'] = row[0]
        #stock['unit_price']=1           
        available_stocks[stock_id] = stock

    for line in owned_stocks.items():
        print(line)

    for line in available_stocks.items():
        print(line)

    st=("select available_balance from users where username = '" + username + "';")
    cursor.execute(st)
    row = (cursor.fetchone()) # Convert to str, trim by starting from the 2nd character, skip last two, convert to int
    available_balance=row[0]
         
    conn.close()

    total_account_worth = round(worth_of_stocks + available_balance,2)
    worth_of_stocks = round(worth_of_stocks,2)
    available_balance=round(available_balance,2)


    return render_template("user-home-page.html",name=name,total_account_worth=total_account_worth,worth_of_stocks=worth_of_stocks,username=username, available_balance=available_balance,owned_stocks=owned_stocks,available_stocks=available_stocks)
    
    

@app.route("/sign-up",methods=['GET', 'POST'])
def signup():       
    return render_template("signup-page.html")

@app.route("/validate-sign-up",methods=['GET', 'POST'])
def check_signup():   
    conn = sqlite3.connect(r"C:\xampp\htdocs\phpLiteAdmin\stock_market")
    cursor = conn.cursor()
    username=request.form.get("username")
    password=request.form.get("password")
    email=request.form.get("email")
    phone=request.form.get("phone number")
    fname=request.form.get("first name")
    lname=request.form.get("last name")

    st=("insert into users (username, password, fname, lname, phone, email, available_balance) values ('" + username + "','" + password + "','" + fname + "','" + lname + "'," + phone + ",'" + email + "',"+ init_balance + ")")
    cursor.execute(st)
    conn.commit()
    
    conn.close()
    return render_template("success.html")


@app.route("/sell_stock",methods=['GET', 'POST'])
def sell_stock():           
    username=request.form.get("username")
    print("sell stocks My Username is: ",username)
    for key in request.form:
        (stock_id,num_of_shares) = (key,request.form.get(key))
        if num_of_shares and re.match("[0-9]",num_of_shares):
            print(stock_id,num_of_shares)
            
            conn = sqlite3.connect(r"C:\xampp\htdocs\phpLiteAdmin\stock_market")
            cursor = conn.cursor()
            st="select stock_code from stocks where stock_id = '" + stock_id + "';"
            cursor.execute(st)
            row = (cursor.fetchone())
            stock_code = row[0]
            st=("select share_price from stocks where stock_id =" + str(stock_id) + ";")
            cursor.execute(st)
            row = (cursor.fetchone())
            unit_price = row[0]            

            st = "select user_id from users where username = '" + username + "';"
            cursor.execute(st)
            row = (cursor.fetchone())
            user_id=row[0]

            st = ("select num_of_shares from purchased_stocks where user_id = " + str(user_id) + " and stock_id = " + str(stock_id) +  ";" )
            cursor.execute(st)
            row = (cursor.fetchone())
            owned_shares=row[0]

            if owned_shares == int(num_of_shares):
                st = ("delete from purchased_stocks where user_id = " + str(user_id) + " and stock_id = " + str(stock_id) +  ";" ) 
                cursor.execute(st)
                conn.commit()
            else:
                owned_shares = owned_shares - int(num_of_shares)
                st = ("update purchased_stocks set num_of_shares = " + str(owned_shares) + " where user_id = " + str(user_id) + " and stock_id = " + str(stock_id) +  ";" ) 
                cursor.execute(st)
            st = ("select available_balance from users where user_id = " + str(user_id) +  ";" )
            cursor.execute(st)
            row = (cursor.fetchone())
            available_balance=row[0]
            
            stock_cost = float(num_of_shares)*float(unit_price)
            st = ("update users set available_balance = " + str(available_balance + stock_cost) + " where user_id = " + str(user_id) +  ";" )
            cursor.execute(st)
            conn.commit()

            print (stock_code, unit_price, user_id, owned_shares)
    
    print(username)
    return render_template("successful_operation.html",username=username)
        
@app.route("/buy_stock",methods=['GET', 'POST'])
def buy_stock():           
    print("I am here")
    username=request.form.get("username")
    print("buy stocks My Username is: ",username)
    for key in request.form:
        (stock_id,num_of_shares) = (key,request.form.get(key))
        if num_of_shares and re.match("[0-9]",num_of_shares):
            print(stock_id,num_of_shares)
            stock_id=stock_id[:-1]
            print (stock_id)            

            conn = sqlite3.connect(r"C:\xampp\htdocs\phpLiteAdmin\stock_market")
            cursor = conn.cursor()
            st="select stock_code, share_price from stocks where stock_id = '" + stock_id + "';"
            cursor.execute(st)
            row = (cursor.fetchone())
            if row:
                stock_code = row[0]
                unit_price = row[1]

            st = "select user_id from users where username = '" + username + "';"
            cursor.execute(st)
            row = (cursor.fetchone())
            user_id=row[0]

            st = ("select num_of_shares from purchased_stocks where user_id = " + str(user_id) + " and stock_id = " + str(stock_id) +  ";" )
            cursor.execute(st)
            row = (cursor.fetchone())

            if row is None:
                owned_shares=0
                st = ("insert into purchased_stocks values (" + str(user_id) + ", " + str(stock_id) +  ", " + str(num_of_shares) + ");" ) 
                print (st)
            else:
                owned_shares=row[0]
                new_shares = int(owned_shares) + int(num_of_shares)
                st = ("update purchased_stocks set num_of_shares = " + str(new_shares) + " where user_id = " + str(user_id) + " and stock_id = " + str(stock_id) + ";" ) 
                print (st)

            cursor.execute(st)

            st = ("select available_balance from users where user_id = " + str(user_id) +  ";" )
            cursor.execute(st)
            row = (cursor.fetchone())
            available_balance=row[0]

            stock_cost = float(num_of_shares)*float(unit_price)
            st = ("update users set available_balance = " + str(available_balance - stock_cost) + " where user_id = " + str(user_id) +  ";" )
            cursor.execute(st)

            conn.commit()

            print (stock_code, unit_price, user_id, owned_shares)
    
    print(username)
    return render_template("successful_operation.html",username=username)
        
@app.route("/account_view",methods=['GET', 'POST'])
def account_view():           
    username=request.form.get("username")
    print(username,"from accountview")
    return check_login(username)

@app.route("/registrants")
def registrants():   
    students=[]     
    conn = sqlite3.connect(r"C:\xampp\htdocs\phpLiteAdmin\registrants")
    cursor = conn.cursor()
    cursor.execute("SELECT fname, lname, major_name, dorm_name from students, major, dorms where students.major_id=major.major_id and students.dorm_id=dorms.dorm_id;") 
    for (fname,lname,major,dorm) in (cursor.fetchall()):
        students.append(fname + " " + lname + " studying " + major + " lives in " + dorm)   
    conn.close()
    return render_template("registrants.html",students=students)

@app.route("/register", methods=["POST"])
def register():
    name=request.form.get("name")
    dorm=request.form.get("dorm")
    
    if not name or not dorm:
        return render_template("failure.html")
    
    # I am good to add people to the Database        
    conn = sqlite3.connect(r"C:\xampp\htdocs\phpLiteAdmin\registrants")
    cursor = conn.cursor()
    cursor.execute("SELECT max(student_id) from students;")   
    id_tuple = (cursor.fetchone()) # Convert to str, trim by starting from the 2nd character, skip last two, convert to int

    #id = (int)((str)(cursor.fetchone())[1:-2]) # Convert to str, trim by starting from the 2nd character, skip last two, convert to int
    for i in id_tuple:
        id=i

    cursor.execute("insert into students (student_id,fname,lname,phone,email,major_id,birthday,dorm_id) values (?,?,?,4041111111,?,1,?,1)",(id+1,name,name,name + "@gmail.com","2001-01-01"))
    conn.commit()
    conn.close()

    return redirect ("/registrants")