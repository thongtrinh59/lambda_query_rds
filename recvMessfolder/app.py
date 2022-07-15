import json
import boto3
import csv
import io
from numpy import NaN
import pandas as pd 
from pandas import DataFrame
import awswrangler as wr
# import pyodbc
from datetime import datetime
import typing
from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy import text
from sqlalchemy import Table, Column, String, MetaData, Integer
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

sqsClient = boto3.client('sqs')
    
# engine = create_engine("mssql+pyodbc://admin:23101994Thong@database-test-thong.cde8dhcc2ppw.ap-southeast-2.rds.amazonaws.com:1433/mic?driver=ODBC+Driver+17+for+SQL+Server")
# cnxn = engine.connect()


class DB:
    def __init__(self, user, password, host, port, dbname, driver):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.dbname = dbname
        self.driver = driver

        db_string = "mssql+pyodbc://{}:{}@{}:{}/{}?driver={}".format(
            self.user, 
            self.password, 
            self.host, 
            self.port,
            self.dbname,
            self.driver
        )

        self.db = create_engine(db_string)

        self.meta = MetaData(self.db)

        self.employee_table = Table(
            'employee', self.meta,
            Column('employeeNumber', Integer, primary_key=True),
            Column('lastName', String),
            Column('firstName', String),
            Column('extension', String),
            Column('email', String),
            Column('officeCode', Integer),
            Column('reportsTo', Integer),
            Column('jobTitle', String)
        )
    
    def is_table_exist(self, table_name):
        if self.db.has_table(table_name):
            return True
        else:
            return False

    def create_tables(self):
        self.meta.create_all(self.db)
        return True

class Employee(Base):
    __tablename__ = 'employee'
    employeeNumber = Column(Integer, primary_key=True)
    lastName = Column(String(50))
    firstName = Column(String(50))
    extension = Column(String(50))
    email = Column(String(50))
    officeCode = Column(Integer)
    reportsTo = Column(Integer)
    jobTitle = Column(String(50))
    
    # def __repr__(self):
    #     return "<Employee(name='%s', fullname='%s', nickname='%s')>" % (
    #         self.name, self.fullname, self.nickname)

def convert_to_int(value):
    print("this is type of value")
    print(type(value))
    if pd.isna(value):
        cov = None
    else:
        cov = int(value)
    return cov

def lambda_handler(event, context):

    # print(event)

    queue_url = "https://sqs.ap-southeast-2.amazonaws.com/549219412834/bridge.fifo"

    try:
        db_instance = DB(
            user='admin', 
            password='23101994Thong', 
            host='database-test-thong.cde8dhcc2ppw.ap-southeast-2.rds.amazonaws.com', 
            port=1433,
            dbname="mic",
            driver="ODBC+Driver+17+for+SQL+Server"
        )
        if db_instance.is_table_exist("employee"):
            print("already exist")
            pass
        else:
            print("create new table")
            db_instance.create_tables()
    except Exception as e:
        raise e

    Session = sessionmaker(bind=db_instance.db)
    session = Session()
    Base.metadata.create_all(db_instance.db)

    # @classmethod
    # def get_or_create(cls, employeeNumber, lastName, firstName, extension, email, officeCode, reportsTo, jobTitle):
    #     exists = session.query(Employee.employeeNumber).filter_by(employeeNumber=employeeNumber, lastName=lastName, firstName=firstName, 
    #         extension=extension, email=email, officeCode=officeCode, reportsTo=reportsTo, jobTitle=jobTitle).scalar() is not None
    #     if exists:
    #         return session.query(Employee).filter_by(employeeNumber=employeeNumber, lastName=lastName, firstName=firstName, 
    #         extension=extension, email=email, officeCode=officeCode, reportsTo=reportsTo, jobTitle=jobTitle).first()
    #     return cls(name=name)

    for element in event["Records"]:
        body = json.loads(element["body"])
        print(type(body))
        lambda_arn = body["lambda_arn"]
        op = body["data"]["op"]
        print(op)
        employeeNumber = convert_to_int(body["data"]["employeeNumber"])
        lastName = body["data"]["lastName"]
        firstName = body["data"]["firstName"]
        extension = body["data"]["extension"]
        email = body["data"]["email"]
        officeCode = convert_to_int(body["data"]["officeCode"])
        reportsTo = convert_to_int(body["data"]["reportsTo"])
        jobTitle = body["data"]["jobTitle"]


        if op == 'N':
            exists = session.query(Employee).filter_by(employeeNumber=employeeNumber, lastName=lastName, firstName=firstName, 
            extension=extension, email=email, officeCode=officeCode, reportsTo=reportsTo, jobTitle=jobTitle).scalar() is not None

            if exists:
                print("this record already exists")
            else:
                new_employee = Employee(employeeNumber=employeeNumber, lastName=lastName, firstName=firstName, 
                    extension=extension, email=email, officeCode=officeCode, reportsTo=reportsTo, jobTitle=jobTitle)
                session.add(new_employee)
                session.commit()

        elif op == "U":
            exists = session.query(Employee).filter_by(employeeNumber=employeeNumber).scalar() is not None
            print("this is exists")
            print(exists)
            if exists:
                temp_employee = session.query(Employee).filter_by(employeeNumber=employeeNumber)
                print(temp_employee)
                temp_employee.lastName = lastName
                temp_employee.firstName = firstName
                temp_employee.extension = extension
                temp_employee.email = email
                temp_employee.officeCode = officeCode
                temp_employee.reportsTo = reportsTo
                temp_employee.jobTitle = jobTitle
                print(temp_employee)
                print('pass')
            else:
                print("insert new data")
                print(type(employeeNumber))
                print(type(officeCode))
                print(type(reportsTo))


                new_employee = Employee(employeeNumber=employeeNumber, lastName=lastName, firstName=firstName, 
                    extension=extension, email=email, officeCode=officeCode, reportsTo=reportsTo, jobTitle=jobTitle)
                session.add(new_employee)
                session.commit()
        elif op == "D":
            exists = session.query(Employee).filter_by(employeeNumber=employeeNumber, lastName=lastName, firstName=firstName, 
                    extension=extension, email=email, officeCode=officeCode, reportsTo=reportsTo, jobTitle=jobTitle).scalar() is not None
            if exists:
                del_employee = session.query(Employee).filter_by(employeeNumber=employeeNumber, lastName=lastName, firstName=firstName, 
                    extension=extension, email=email, officeCode=officeCode, reportsTo=reportsTo, jobTitle=jobTitle).first()
                session.delete(del_employee)
                session.commit()
            else:
                pass


    # td = "select * from khan"
    # result = cnxn.execute(td)
    # rows = result.fetchall()
    # print(rows)

        

    # except Exception as e:
    #     raise e 



    return None
